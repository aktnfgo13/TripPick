plugins {
    id("com.android.application") version "8.5.2"
    id("org.jetbrains.kotlin.android") version "1.9.24"
}

android {
    namespace = "kr.trippick"
    compileSdk = 34
    defaultConfig {
        applicationId = "kr.trippick.vehicle"
        minSdk = 28
        targetSdk = 34
        versionCode = 1
        versionName = "0.1"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.14" }
}

dependencies {
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.3")
    implementation("androidx.compose.material:material:1.6.8")
    if (providers.gradleProperty("withPleosSdk").orNull == "true") {
        implementation("ai.pleos.playground:Vehicle:2.3.2")
    }
    testImplementation("junit:junit:4.13.2")
}
