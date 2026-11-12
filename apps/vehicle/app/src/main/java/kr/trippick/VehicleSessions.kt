package kr.trippick

import android.content.Context
import org.json.JSONObject

/** Private app storage. Each trip keeps its vehicle credentials when switching trips. */
class VehicleSessions(context: Context) {
    private val prefs = context.getSharedPreferences("travel", 0)
    val current
        get() = prefs.getString("trip", "").orEmpty()

    val token
        get() = prefs.getString("vehicleToken", "").orEmpty()

    val selected
        get() = prefs.getString("selected", "").orEmpty()

    fun code(kind: String) = prefs.getString(kind, "").orEmpty()

    fun remember(title: String, data: JSONObject) {
        val trip = data.getString("tripId")
        val entry =
            JSONObject()
                .put("title", title)
                .put("vehicleToken", data.getString("vehicleToken"))
                .put("invite", data.getString("inviteToken"))
                .put("claim", data.getString("claimToken"))
        prefs.edit().putString("saved/" + trip, entry.toString()).apply()
        switch(trip)
    }

    fun switch(trip: String) {
        val entry = JSONObject(prefs.getString("saved/" + trip, null) ?: error("저장된 여행 없음"))
        prefs
            .edit()
            .putString("trip", trip)
            .putString("vehicleToken", entry.getString("vehicleToken"))
            .putString("invite", entry.getString("invite"))
            .putString("claim", entry.getString("claim"))
            .putString("selected", prefs.getString("detail/" + trip, ""))
            .apply()
    }

    fun leaveCurrent() {
        prefs
            .edit()
            .remove("trip")
            .remove("vehicleToken")
            .remove("invite")
            .remove("claim")
            .remove("selected")
            .apply()
    }

    fun saveDetail(id: String) {
        prefs.edit().putString("selected", id).putString("detail/" + current, id).apply()
    }

    fun saved(): Map<String, String> =
        prefs.all.entries
            .filter { it.key.startsWith("saved/") }
            .associate {
                it.key.removePrefix("saved/") to JSONObject(it.value.toString()).getString("title")
            }
}
