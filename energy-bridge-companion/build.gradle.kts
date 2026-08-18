plugins {
    id("com.android.application")
}

android {
    namespace = "dev.rosinski.watchface.companion"
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.rosinski.watchface.companion"
        minSdk = 28
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
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("com.google.android.gms:play-services-wearable:19.0.0")
}
