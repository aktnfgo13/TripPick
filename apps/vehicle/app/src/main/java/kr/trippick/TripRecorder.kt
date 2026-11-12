package kr.trippick

import android.content.Context
import java.time.Instant
import java.util.UUID
import org.json.JSONObject

/** Keep the active destination identity across reconnects; an arrival has no coordinates. */
class TripRecorder(context: Context) {
    private val prefs = context.getSharedPreferences("journal", 0)

    fun enabled(trip: String) = trip.isNotEmpty() && prefs.getBoolean("on/" + trip, false)

    fun toggle(trip: String) {
        if (!enabled(trip)) prefs.edit().remove("target/" + trip).apply()
        prefs.edit().putBoolean("on/" + trip, !enabled(trip)).apply()
    }

    fun observation(trip: String, e: NavigationObservation): JSONObject? {
        if (!enabled(trip) || e.name.isBlank()) return null
        val previous = prefs.getString("target/" + trip, null)?.let(::JSONObject)
        val arrived = e.kind == "ARRIVED"
        val location = e.kind == "LOCATION"
        val same =
            previous != null &&
                previous.optString("name") == e.name &&
                ((arrived && previous.optString("address") == e.address) ||
                    (previous.optDouble("latitude") == e.latitude &&
                        previous.optDouble("longitude") == e.longitude))
        if (
            !arrived &&
                (e.latitude == null ||
                    e.longitude == null ||
                    e.latitude !in -90.0..90.0 ||
                    e.longitude !in -180.0..180.0 ||
                    (e.latitude == 0.0 && e.longitude == 0.0))
        )
            return null
        if (location && previous != null) return null
        val saved =
            if (same && !location) previous!!
            else
                JSONObject()
                    .put(
                        "key",
                        if (location)
                            "location-" +
                                Instant.now().epochSecond.div(3600) +
                                "-" +
                                e.latitude +
                                "-" +
                                e.longitude
                        else UUID.randomUUID().toString(),
                    )
                    .put("name", e.name)
                    .put("address", e.address)
                    .put("latitude", e.latitude)
                    .put("longitude", e.longitude)
        if (!location) prefs.edit().putString("target/" + trip, saved.toString()).apply()
        return JSONObject(saved.toString())
            .put("kind", if (arrived) "ARRIVED" else "CANDIDATE")
            .put("source", if (e.simulated) "MOCK" else if (location) "LOCATION" else "NAVIGATION")
            .put("observedAt", Instant.now().toString())
    }
}
