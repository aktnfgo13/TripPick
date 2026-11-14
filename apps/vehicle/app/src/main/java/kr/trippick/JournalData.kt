package kr.trippick

import android.content.Context
import org.json.JSONObject
import org.json.JSONArray
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class Point(val x: Double, val y: Double)

data class Region(val code: String, val name: String, val rings: List<List<Point>>, val predecessors: List<String> = emptyList())

data class Stop(
    val id: String,
    val place: String,
    val name: String,
    val region: String,
    val point: Point?,
    val time: String,
    val state: String,
    val category: String,
    val source: String,
)

data class Journal(
    val regions: List<Region>,
    val stops: List<Stop>,
    val links: Map<String, List<String>>,
)

internal fun Journal.restoreRoute(region: String, place: String): Pair<String, String> {
    val active = regions.firstOrNull { it.code == region || region in it.predecessors }?.code ?: return "" to ""
    val validPlace = place.takeIf { id -> stops.any { it.place == id && it.region == active } }
    return active to validPlace.orEmpty()
}

private fun rings(polygon: JSONArray): List<List<Point>> =
    (0 until polygon.length()).map { i ->
        val ring = polygon.getJSONArray(i)
        (0 until ring.length()).map { j ->
            val xy = ring.getJSONArray(j)
            Point(xy.getDouble(0) * 0.8, -xy.getDouble(1))
        }
    }

class JournalData(private val api: VehicleApi = VehicleApi()) {
    suspend fun edit(trip: String, token: String, visit: String, status: String, name: String?) {
        api.request(
            "/trips/" + trip + "/visits/" + visit,
            token,
            "PATCH",
            org.json.JSONObject().put("status", status).put("name", name),
        )
    }

    suspend fun bundled(context: Context): List<Region> = withContext(Dispatchers.IO) {
        fun asset(name: String) = context.assets.open(name).bufferedReader().use { JSONObject(it.readText()) }
        val features = asset("korea.geojson").getJSONArray("features")
        val changes = asset("catalog.json").getJSONArray("changes")
        fun region(properties: JSONObject, geometry: JSONObject): Region {
            val coordinates = geometry.getJSONArray("coordinates")
            val polygons = if (geometry.getString("type") == "Polygon") rings(coordinates)
                else (0 until coordinates.length()).flatMap { rings(coordinates.getJSONArray(it)) }
            val old = properties.optJSONArray("predecessors")
            return Region(properties.getString("code"), properties.getString("name"), polygons,
                old?.let { (0 until it.length()).map(it::getString) }.orEmpty())
        }
        val replacements = (0 until changes.length()).map {
            val change = changes.getJSONObject(it)
            region(change, asset(change.getString("geometry")))
        }
        val retired = replacements.flatMap { it.predecessors }.toSet()
        (0 until features.length()).map {
            val feature = features.getJSONObject(it)
            region(feature.getJSONObject("properties"), feature.getJSONObject("geometry"))
        }.filter { it.code !in retired }.plus(replacements).sortedBy { it.code }
    }

    suspend fun fetch(trip: String, token: String) = api.request("/trips/" + trip + "/journal", token)

    fun journal(shapes: List<Region>, data: JSONObject): Journal {
        val visits = data.getJSONArray("visits")
        val stops =
            (0 until visits.length())
                .map { i ->
                    val v = visits.getJSONObject(i)
                    Stop(
                        v.getString("id"),
                        v.getString("place_id"),
                        v.getString("name"),
                        shapes.firstOrNull { v.optString("region_code") in it.predecessors }?.code ?: v.optString("region_code"),
                        if (v.isNull("latitude")) null
                        else Point(v.getDouble("longitude") * .8, -v.getDouble("latitude")),
                        v.getString("observed_at"),
                        v.getString("status"),
                        v.getString("category"),
                        v.getString("source"),
                    )
                }
                .filter { it.state != "EXCLUDED" }
        val links = data.getJSONArray("links")
        return Journal(
            shapes,
            stops,
            (0 until links.length())
                .map { links.getJSONObject(it) }
                .filter { !it.isNull("visit_id") }
                .groupBy({ it.getString("visit_id") }, { it.getString("photo_id") }),
        )
    }
}
