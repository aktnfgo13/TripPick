@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

package kr.trippick

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import kotlin.math.*
import kotlinx.coroutines.launch

@Composable
fun JournalMap(model: TravelModel, back: () -> Unit) {
    val cache = LocalContext.current.getSharedPreferences("journal-view", 0)
    val trip = model.trip
    val repository = remember { JournalData() }
    var data by remember { mutableStateOf<Journal?>(null) }
    var error by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    var albumOpen by rememberSaveable(trip) { mutableStateOf(false) }
    var editName by remember { mutableStateOf<String?>(null) }
    var refresh by remember { mutableIntStateOf(0) }
    var region by
        rememberSaveable(trip) { mutableStateOf(cache.getString("region/" + trip, "").orEmpty()) }
    var place by
        rememberSaveable(trip) { mutableStateOf(cache.getString("place/" + trip, "").orEmpty()) }
    fun chooseRegion(code: String) {
        region = code
        place = ""
        albumOpen = false
        cache.edit().putString("region/" + trip, code).remove("place/" + trip).apply()
    }
    fun choosePlace(id: String) {
        place = id
        albumOpen = false
        cache.edit().putString("place/" + trip, id).apply()
    }
    LaunchedEffect(trip, refresh) {
        runCatching { repository.load(trip, model.token) }
            .onSuccess {
                val route = it.restoreRoute(region, place)
                if (route.first != region) chooseRegion(route.first)
                else if (route.second != place) choosePlace(route.second)
                data = it
                error = ""
            }
            .onFailure { error = it.message ?: "지도 조회 실패" }
    }
    Column(Modifier.fillMaxSize().padding(8.dp).verticalScroll(rememberScrollState())) {
        FlowRow {
            TextButton(onClick = back) { Text("지도 닫기") }
            TextButton(onClick = { chooseRegion("") }) { Text("전국 지도") }
            TextButton(onClick = { refresh++ }) { Text("지도 새로고침") }
        }
        if (error.isNotEmpty()) Text(error)
        val journal = data
        if (journal == null) {
            Text("지도 불러오는 중")
            return@Column
        }
        val places = journal.stops.distinctBy { it.place }
        val selected = journal.regions.firstOrNull { it.code == region }
        Text(selected?.name ?: "대한민국", style = MaterialTheme.typography.h6)
        // Region selectors stay above the map so all 17 are accessible in a small window.
        if (selected == null)
            FlowRow {
                journal.regions.forEach { r ->
                    TextButton(onClick = { chooseRegion(r.code) }) {
                        Text(r.name + " " + places.count { it.region == r.code })
                    }
                }
            }
        else
            FlowRow {
                places
                    .filter { it.region == region }
                    .forEach { v ->
                        TextButton(onClick = { choosePlace(v.place) }) { Text(v.name) }
                    }
            }
        val visits = journal.stops.filter { it.place == place }
        if (visits.isNotEmpty()) {
            val photos = visits.flatMap { journal.links[it.id].orEmpty() }.distinct()
            Text(
                visits.first().name + " · " + visits.first().category + " · 사진 " + photos.size + "장"
            )
            if (photos.isNotEmpty()) {
                Preview(model, photos.first(), Modifier.size(82.dp))
                TextButton(onClick = { albumOpen = !albumOpen }) {
                    Text(if (albumOpen) "장소 앨범 닫기" else "장소 앨범 열기")
                }
                if (albumOpen)
                    LazyRow {
                        items(photos, key = { it }) { photo ->
                            Preview(
                                model,
                                photo,
                                Modifier.size(100.dp).clickable {
                                    model.select(photo)
                                    back()
                                },
                            )
                        }
                    }
            }
            fun edit(status: String, name: String? = null) {
                scope.launch {
                    runCatching {
                            repository.edit(trip, model.token, visits.first().id, status, name)
                        }
                        .onSuccess {
                            editName = null
                            refresh++
                        }
                        .onFailure { error = it.message ?: "수정 실패" }
                }
            }
            if (model.role == "owner") {
                FlowRow {
                    TextButton(onClick = { editName = visits.first().name }) { Text("장소 수정") }
                    TextButton(onClick = { edit("EXCLUDED") }) { Text("이번 방문 제외") }
                }
                editName?.let { name ->
                    OutlinedTextField(name, { editName = it }, label = { Text("장소명") })
                    TextButton(onClick = { edit("CONFIRMED", name) }, enabled = name.isNotBlank()) {
                        Text("방문 확인·저장")
                    }
                }
            }
            Text("여행일지")
            visits.forEach { v ->
                val date =
                    runCatching {
                            Instant.parse(v.time)
                                .atZone(ZoneId.systemDefault())
                                .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"))
                        }
                        .getOrDefault(v.time)
                Text(
                    date +
                        " · " +
                        mapOf("CANDIDATE" to "후보", "ARRIVED" to "도착 확인", "CONFIRMED" to "사용자 확인")[
                            v.state] +
                        " · " +
                        v.source
                )
            }
        }
        key(region) {
            Geography(
                selected?.let { listOf(it) } ?: journal.regions,
                places,
                selected != null,
                ::chooseRegion,
                ::choosePlace,
            )
        }
        Text("geoBoundaries · Natural Earth · 2021", style = MaterialTheme.typography.caption)
    }
}
