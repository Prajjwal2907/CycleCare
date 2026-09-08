package com.cyclecare.healthconnect

import android.content.Context
import androidx.activity.ComponentActivity
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.PermissionController
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.SleepSessionRecord
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import androidx.health.connect.client.permission.HealthPermission
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.time.Instant
import java.time.ZoneId
import java.time.temporal.ChronoUnit
import kotlin.coroutines.resume

/**
 * Reads Health Connect data and sends the normalized payload to CycleCare.
 *
 * Add the Health Connect SDK dependency and health permissions described in
 * app/android/README.md before using this class in an Android module.
 */
class HealthConnectFetcher(
    context: Context,
    private val backendBaseUrl: String = "http://10.0.2.2:8000"
) {
    private val client = HealthConnectClient.getOrCreate(context.applicationContext)
    private val zone = ZoneId.systemDefault()

    companion object {
        val REQUIRED_PERMISSIONS = setOf(
            HealthPermission.getReadPermission(SleepSessionRecord::class),
            HealthPermission.getReadPermission(StepsRecord::class),
            HealthPermission.getReadPermission(ExerciseSessionRecord::class)
        )
    }

    suspend fun requestPermissions(activity: ComponentActivity): Set<String> =
        suspendCancellableCoroutine { continuation ->
            val launcher = activity.activityResultRegistry.register(
                "cyclecare-health-connect-permissions",
                PermissionController.createRequestPermissionResultContract()
            ) { granted ->
                if (continuation.isActive) continuation.resume(granted)
            }
            continuation.invokeOnCancellation { launcher.unregister() }
            launcher.launch(REQUIRED_PERMISSIONS)
        }

    suspend fun hasRequiredPermissions(): Boolean {
        val granted = client.permissionController.getGrantedPermissions()
        return granted.containsAll(REQUIRED_PERMISSIONS)
    }

    suspend fun syncLastDays(accessToken: String, days: Long = 7): SyncResult {
        require(days in 1..90) { "days must be between 1 and 90" }
        check(hasRequiredPermissions()) { "Health Connect permissions have not been granted" }

        val end = Instant.now()
        val start = end.minus(days, ChronoUnit.DAYS)
        val range = TimeRangeFilter.between(start, end)
        val sleepRecords = client.readRecords(
            ReadRecordsRequest(SleepSessionRecord::class, timeRangeFilter = range)
        ).records
        val exerciseRecords = client.readRecords(
            ReadRecordsRequest(ExerciseSessionRecord::class, timeRangeFilter = range)
        ).records
        val stepRecords = client.readRecords(
            ReadRecordsRequest(StepsRecord::class, timeRangeFilter = range)
        ).records

        val sleepByDate = mutableMapOf<String, JSONObject>()
        sleepRecords.forEach { record ->
            val date = record.startTime.atZone(zone).toLocalDate()
            val total = ChronoUnit.MINUTES.between(record.startTime, record.endTime).coerceAtLeast(0)
            val deep = record.stages
                .filter { it.stage == SleepSessionRecord.STAGE_TYPE_DEEP }
                .sumOf { ChronoUnit.MINUTES.between(it.startTime, it.endTime).coerceAtLeast(0) }
            val rem = record.stages
                .filter { it.stage == SleepSessionRecord.STAGE_TYPE_REM }
                .sumOf { ChronoUnit.MINUTES.between(it.startTime, it.endTime).coerceAtLeast(0) }
            val light = (total - deep - rem).coerceAtLeast(0)
            val daily = sleepByDate.getOrPut(date.toString()) {
                JSONObject().apply {
                    put("date", date.toString())
                    put("total_sleep_minutes", 0)
                    put("deep_sleep_minutes", 0)
                    put("rem_sleep_minutes", 0)
                    put("light_sleep_minutes", 0)
                }
            }
            daily.put("total_sleep_minutes", daily.getLong("total_sleep_minutes") + total)
            daily.put("deep_sleep_minutes", daily.getLong("deep_sleep_minutes") + deep)
            daily.put("rem_sleep_minutes", daily.getLong("rem_sleep_minutes") + rem)
            daily.put("light_sleep_minutes", daily.getLong("light_sleep_minutes") + light)
        }

        val exerciseByActivity = mutableMapOf<String, JSONObject>()
        exerciseRecords.forEach { record ->
            val minutes = ChronoUnit.MINUTES.between(record.startTime, record.endTime).coerceAtLeast(0)
            val date = record.startTime.atZone(zone).toLocalDate().toString()
            val activity = exerciseName(record.exerciseType)
            val daily = exerciseByActivity.getOrPut("$date|$activity") {
                JSONObject().apply {
                    put("date", date)
                    put("activity_type", activity)
                    put("duration_minutes", 0)
                    put("intensity", "medium")
                }
            }
            daily.put("duration_minutes", daily.getLong("duration_minutes") + minutes)
        }
        stepRecords.groupBy { it.startTime.atZone(zone).toLocalDate() }.forEach { (date, records) ->
            val steps = records.sumOf { it.count }
            exerciseByActivity["$date|steps"] = JSONObject().apply {
                put("date", date.toString())
                put("activity_type", "steps")
                put("duration_minutes", 0)
                put("intensity", if (steps >= 10000) "high" else if (steps >= 5000) "medium" else "low")
                put("calories_burned", JSONObject.NULL)
            }
        }

        val sleep = JSONArray().apply { sleepByDate.values.forEach { put(it) } }
        val exercise = JSONArray().apply { exerciseByActivity.values.forEach { put(it) } }

        val payload = JSONObject().apply {
            put("provider", "health_connect")
            put("sleep", sleep)
            put("exercise", exercise)
            put("alcohol", JSONArray())
        }
        return postSync(payload, accessToken)
    }

    private suspend fun postSync(payload: JSONObject, accessToken: String): SyncResult = withContext(Dispatchers.IO) {
        val connection = (URL("${backendBaseUrl.trimEnd('/')}/api/wearables/sync/").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 10_000
            readTimeout = 20_000
            doOutput = true
            setRequestProperty("Authorization", "Bearer $accessToken")
            setRequestProperty("Content-Type", "application/json")
        }
        try {
            connection.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) }
            val responseCode = connection.responseCode
            val body = (if (responseCode in 200..299) connection.inputStream else connection.errorStream)
                .bufferedReader().use { it.readText() }
            if (responseCode !in 200..299) error("Wearable sync failed ($responseCode): $body")
            val json = JSONObject(body).getJSONObject("synced")
            SyncResult(
                sleepRecords = json.optInt("sleep_records"),
                exerciseRecords = json.optInt("exercise_records"),
                alcoholSignals = json.optInt("alcohol_signals")
            )
        } finally {
            connection.disconnect()
        }
    }

    private fun exerciseName(type: Int): String = when (type) {
        ExerciseSessionRecord.EXERCISE_TYPE_WALKING -> "walking"
        ExerciseSessionRecord.EXERCISE_TYPE_RUNNING -> "running"
        ExerciseSessionRecord.EXERCISE_TYPE_BIKING -> "cycling"
        ExerciseSessionRecord.EXERCISE_TYPE_SWIMMING -> "swimming"
        else -> "workout"
    }
}

data class SyncResult(
    val sleepRecords: Int,
    val exerciseRecords: Int,
    val alcoholSignals: Int
)
