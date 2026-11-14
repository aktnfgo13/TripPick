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
    val context = LocalContext.current
    val cache = context.getSharedPreferences("journal-view", 0)
    val trip = model.trip
    val repository = remember { JournalData() }
    val credential = model.token
    var sync by remember(trip, credential) { mutableStateOf("기본 지도") }
    var online by remember(trip, credential) { mutableStateOf(false) }
    var data by remember(trip, credential) { mutableStateOf<Journal?>(null) }
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
    androidx.activity.compose.BackHandler {
        when {
            place.isNotEmpty() -> choosePlace("")
            region.isNotEmpty() -> chooseRegion("")
            else -> back()
        }
    }
    LaunchedEffect(trip, credential, refresh) {
        val shapes = runCatching { repository.bundled(context) }.getOrElse {
            error = "앱의 지도 파일을 열 수 없습니다."
            return@LaunchedEffect
        }
        val base = Journal(shapes, emptyList(), emptyMap())
        data = base
        region = base.restoreRoute(region, "").first
        if (trip.isBlank() || credential.isBlank()) return@LaunchedEffect
        val digest = java.security.MessageDigest.getInstance("SHA-256")
            .digest((BuildConfig.API_ORIGIN + "/" + trip + "/" + credential).toByteArray())
        val snapshot = "snapshot/" + android.util.Base64.encodeToString(digest, android.util.Base64.NO_WRAP)
        val cached = cache.getString(snapshot, null)?.let {
            runCatching { repository.journal(shapes, org.json.JSONObject(it)) }.getOrNull()
        }
        data = cached ?: base
        online = false
        error = ""
        sync = if (cached == null) "방문 기록 동기화 중" else "저장된 기록 · 동기화 중"
        try {
            val response = repository.fetch(trip, credential)
            val journal = repository.journal(shapes, response)
            cache.edit().putString(snapshot, response.toString()).apply()
            data = journal
            val route = journal.restoreRoute(region, place)
            if (route.second != place) choosePlace(route.second)
            sync = "방문 기록 · 동기화 완료"
            online = true
        } catch (e: kotlinx.coroutines.CancellationException) {
            throw e
        } catch (e: Exception) {
            if (e is VehicleResponseError && e.status in listOf(401, 403, 404)) {
                cache.edit().remove(snapshot).apply()
                data = base
                sync = "여행 접근 권한을 확인하세요"
            } else {
                val reason = if (e is java.io.IOException) "오프라인" else "동기화 실패"
                sync = reason + if (cached == null) " · 저장된 방문 기록 없음" else " · 마지막 저장 기록"
            }
        }
    }
    Column(Modifier.fillMaxSize().padding(8.dp).verticalScroll(rememberScrollState())) {
        FlowRow {
            TextButton(onClick = back) { Text("지도 닫기") }
            TextButton(onClick = { chooseRegion("") }) { Text("전국 지도") }
            TextButton(onClick = { refresh++ }) { Text("지도 새로고침") }
        }
        Text(sync, style = MaterialTheme.typography.subtitle1)
        if (error.isNotEmpty()) Text(error)
        val journal = data
        if (journal == null) {
            if (error.isEmpty()) Text("지도 불러오는 중")
            return@Column
        }
        val places = journal.stops.sortedBy { it.state == "CANDIDATE" }.distinctBy { it.place }
        val selected = journal.regions.firstOrNull { it.code == region }
        Text(selected?.name ?: "대한민국", style = MaterialTheme.typography.h6)
        if (selected != null && (online || journal.stops.isNotEmpty())) Text("방문 확인 " + places.count { it.region == region && it.state in listOf("CONFIRMED", "ARRIVED") } + "곳 · 후보 " + places.count { it.region == region && it.state == "CANDIDATE" } + "곳")
        key(region) {
            Geography(
                selected?.let { listOf(it) } ?: journal.regions,
                places,
                selected != null,
                ::chooseRegion,
                ::choosePlace,
            )
        }

        if (selected == null)
            FlowRow {
                journal.regions.forEach { r ->
                    TextButton(onClick = { chooseRegion(r.code) }) {
                        Text(r.name + if (online || journal.stops.isNotEmpty()) " " + places.count { it.region == r.code && it.state in listOf("CONFIRMED", "ARRIVED") } else "")
                    }
                }
            }
        else
            FlowRow {
                places
                    .filter { it.region == region }
                    .forEach { v ->
                        TextButton(onClick = { choosePlace(v.place) }) { Text(v.name + if (v.state == "CANDIDATE") " · 후보" else "") }
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
            if (online && model.role == "owner") {
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
        Text("2021 행정경계 · geoBoundaries CC BY 4.0 · Natural Earth PD", style = MaterialTheme.typography.caption)
    }
}
