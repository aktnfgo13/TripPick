package kr.trippick

import org.json.JSONArray

data class Point(val x: Double, val y: Double)

data class Region(val code: String, val name: String, val rings: List<List<Point>>)

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
    if (regions.none { it.code == region }) return "" to ""
    val validPlace = place.takeIf { id -> stops.any { it.place == id && it.region == region } }
    return region to validPlace.orEmpty()
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

    private var regions: List<Region>? = null

    suspend fun load(trip: String, token: String): Journal {
        val shapes =
            regions
                ?: run {
                    val features = api.request("/regions").getJSONArray("features")
                    (0 until features.length())
                        .map { i ->
                            val f = features.getJSONObject(i)
                            val p = f.getJSONObject("properties")
                            val g = f.getJSONObject("geometry")
                            val coordinates = g.getJSONArray("coordinates")
                            Region(
                                p.getString("code"),
                                p.getString("name"),
                                if (g.getString("type") == "Polygon") rings(coordinates)
                                else
                                    (0 until coordinates.length()).flatMap {
                                        rings(coordinates.getJSONArray(it))
                                    },
                            )
                        }
                        .also { regions = it }
                }
        val data = api.request("/trips/" + trip + "/journal", token)
        val visits = data.getJSONArray("visits")
        val stops =
            (0 until visits.length())
                .map { i ->
                    val v = visits.getJSONObject(i)
                    Stop(
                        v.getString("id"),
                        v.getString("place_id"),
                        v.getString("name"),
                        v.optString("region_code"),
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
