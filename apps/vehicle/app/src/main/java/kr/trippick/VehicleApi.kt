package kr.trippick

import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class VehicleApi {
    suspend fun request(path:String, token:String="", method:String="GET", body:JSONObject?=null):JSONObject =
        withContext(Dispatchers.IO) {
            val conn=URL(BuildConfig.API_ORIGIN.trimEnd('/')+"/api/v1"+path).openConnection() as HttpURLConnection
            try {
                conn.requestMethod=method
                conn.instanceFollowRedirects=false
                conn.connectTimeout=6000
                conn.readTimeout=8000
                if(token.isNotBlank()) conn.setRequestProperty("Authorization","Bearer "+token)
                if(body!=null){
                    conn.doOutput=true
                    conn.setRequestProperty("Content-Type","application/json")
                    conn.outputStream.use { it.write(body.toString().toByteArray()) }
                }
                if(conn.responseCode !in 200..299) {
                    val detail=conn.errorStream?.bufferedReader()?.use { it.readText() }
                    error(runCatching { JSONObject(detail ?: "{}").getString("detail") }.getOrDefault("HTTP ${conn.responseCode}"))
                }
                conn.inputStream.bufferedReader().use { JSONObject(it.readText()) }
            } finally { conn.disconnect() }
        }
}
