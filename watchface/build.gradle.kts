plugins {
    id("com.android.application")
}

android {
    namespace = "dev.rosinski.watchface.nineeleven"
    // Watch Face Format bundles are resource-only: no Kotlin, no Java, no code.
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.rosinski.watchface.nineeleven"
        // WFF v2 == Wear OS 5 (API 34). The Galaxy Watch Ultra ships with
        // Wear OS 5 / One UI 6 Watch or newer, so v2 is the widest target that
        // still gives us GOAL_PROGRESS complications.
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    androidResources {
        // The PNGs are already optimised by the generator; re-crunching them
        // only costs build time.
        noCompress += "png"
    }
}
