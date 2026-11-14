plugins {
    id("com.android.application") version "8.5.2"
    id("org.jetbrains.kotlin.android") version "1.9.24"
}

val withPleosSdk = providers.gradleProperty("withPleosSdk").orNull == "true"
android {
    sourceSets["main"].assets.srcDir("../../../assets/maps")
    useLibrary("android.car", false)
    sourceSets["main"].java.srcDir(if (withPleosSdk) "src/pleos/java" else "src/base/java")
    if (withPleosSdk) sourceSets["debug"].manifest.srcFile("src/pleosDebug/AndroidManifest.xml")
    if (withPleosSdk) sourceSets["release"].manifest.srcFile("src/pleos/AndroidManifest.xml")
    namespace = "kr.trippick"
    compileSdk = 34
    defaultConfig {
        applicationId = "kr.trippick.vehicle"
        if (providers.gradleProperty("isolatedDemo").orNull == "true") applicationIdSuffix = ".demo"
        minSdk = 28
        targetSdk = 34
        buildConfigField("String","API_ORIGIN","\""+providers.gradleProperty("apiOrigin").getOrElse("http://10.0.2.2:8000")+"\"")
        buildConfigField("String","WEB_ORIGIN","\""+providers.gradleProperty("webOrigin").getOrElse("")+"\"")
        versionCode = 2
        versionName = "0.1"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true; buildConfig = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.14" }
}

dependencies {
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.3")
    implementation("androidx.compose.material:material:1.6.8")
    if (providers.gradleProperty("withPleosSdk").orNull == "true") {
        implementation("ai.pleos.playground:Vehicle:2.3.2")
        implementation("ai.pleos.playground:NaviHelper:3.0.5")
    }
    implementation("com.google.zxing:core:3.5.3")
    implementation("io.coil-kt:coil-compose:2.6.0")
    testImplementation("junit:junit:4.13.2")
}
