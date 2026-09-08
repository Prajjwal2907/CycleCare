# Android Health Connect fetcher

The Android shell has not been initialized yet. `HealthConnectFetcher.kt` is the integration class to copy into a Capacitor/Android module when it is created.

## Gradle dependency

Add the Health Connect and Activity dependencies to the Android module:

```kotlin
dependencies {
    implementation("androidx.health.connect:connect-client:1.1.0-alpha12")
    implementation("androidx.activity:activity-ktx:1.10.1")
}
```

Use versions compatible with the Android project's existing Gradle catalog when Capacitor is initialized.

## Manifest

```xml
<uses-permission android:name="android.permission.health.READ_SLEEP" />
<uses-permission android:name="android.permission.health.READ_STEPS" />
<uses-permission android:name="android.permission.health.READ_EXERCISE" />
```

The app should also declare Health Connect's package visibility if targeting Android 11+:

```xml
<queries>
    <package android:name="com.google.android.apps.healthdata" />
</queries>
```

## Usage

From a `ComponentActivity`, create the fetcher and request permissions:

```kotlin
val fetcher = HealthConnectFetcher(this, "https://api.example.com")
lifecycleScope.launch {
    fetcher.requestPermissions(this@MainActivity)
    val result = fetcher.syncLastDays(accessToken, days = 7)
}
```

For the Android emulator, the default backend URL is `http://10.0.2.2:8000`. A physical device must use the development machine's LAN IP, for example `http://192.168.1.20:8000`, and Django must allow that host.

The fetcher sends normalized records to `POST /api/wearables/sync/` with the logged-in patient's JWT. It reads sleep sessions, exercise sessions, and daily step totals. Alcohol remains empty because Health Connect does not expose a reliable alcohol-vitals record for this integration.
