plugins {
    id("com.android.application")
}

android {
    namespace = "dev.rosinski.watchface.energybridge"
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.rosinski.watchface.energybridge"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("androidx.wear.watchface:watchface-complications-data-source:1.2.1")
    implementation("com.google.android.gms:play-services-wearable:19.0.0")
}
