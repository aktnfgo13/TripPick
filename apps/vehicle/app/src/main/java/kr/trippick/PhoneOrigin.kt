package kr.trippick

import java.net.URI
import java.util.Locale

internal fun validPhoneOrigin(value: String): Boolean {
    val uri = runCatching { URI(value) }.getOrNull() ?: return false
    val host = uri.host?.lowercase(Locale.ROOT)?.trimEnd('.') ?: return false
    return uri.scheme == "https" && uri.rawUserInfo == null && uri.rawQuery == null &&
        uri.rawFragment == null && uri.rawPath.isNullOrEmpty() && uri.port in -1..65535 &&
        host.contains('.') && host != "localhost" && !host.endsWith(".localhost") &&
        !host.startsWith("127.") && host !in setOf("0.0.0.0","10.0.2.2","10.0.2.3")
}
