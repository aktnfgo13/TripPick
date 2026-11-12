package kr.trippick

import android.app.Application
import androidx.compose.runtime.*
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.json.JSONArray
import org.json.JSONObject

data class GalleryPhoto(val id: String, val uploader: String, val count: Int, val voted: Boolean)

internal fun restoredPhoto(selected: String, photos: List<GalleryPhoto>): String =
    selected.takeIf { id -> photos.any { it.id == id } }.orEmpty()

class TravelModel(app: Application) : AndroidViewModel(app) {
    private val recorder = TripRecorder(app)
    private val sessions = VehicleSessions(app)
    val savedTrips
        get() = sessions.saved()

    private var loadedRevision = -1
    private val api = VehicleApi()
    private val mutex = Mutex()
    var trip by mutableStateOf(sessions.current)
        private set

    var recording by mutableStateOf(recorder.enabled(trip))
        private set

    var journalMessage by mutableStateOf("")
        private set

    fun toggleRecording() {
        recorder.toggle(trip)
        recording = recorder.enabled(trip)
    }

    fun observe(e: NavigationObservation) {
        val target = trip
        val credential = token
        val payload = recorder.observation(target, e) ?: return
        viewModelScope.launch {
            runCatching { api.request("/trips/" + target + "/visits", credential, "POST", payload) }
                .onSuccess { journalMessage = "방문 기록 저장" }
                .onFailure { journalMessage = "방문 저장 실패 · 수동 확인 가능" }
        }
    }

    val token
        get() = sessions.token

    var title by mutableStateOf("")
        private set

    var status by mutableStateOf("")
        private set

    var members by mutableStateOf("")
        private set

    var actor by mutableStateOf("")
        private set

    var role by mutableStateOf("")
        private set

    var photos by mutableStateOf(listOf<GalleryPhoto>())
        private set

    var album by mutableStateOf(listOf<String>())
        private set

    var albumRevision by mutableIntStateOf(0)
        private set

    var selected by mutableStateOf(sessions.selected)
        private set

    var error by mutableStateOf("")
        private set

    var busy by mutableStateOf(false)
        private set

    var qr by mutableStateOf("")
        private set

    private val base
        get() = "/trips/" + trip

    private fun run(action: suspend () -> Unit) =
        viewModelScope.launch {
            mutex.withLock {
                busy = true
                try {
                    action()
                    error = ""
                } catch (e: Exception) {
                    error = e.message ?: "연결 실패"
                } finally {
                    busy = false
                }
            }
        }

    fun create(name: String) = run {
        val data = api.request("/trips", method = "POST", body = JSONObject().put("title", name))
        sessions.remember(name, data)
        restore()
    }

    fun reopen(id: String) = run {
        sessions.switch(id)
        restore()
    }

    private suspend fun restore() {
        loadSavedState()
        refreshData()
    }

    private fun loadSavedState() {
        loadedRevision = -1
        trip = sessions.current
        recording = recorder.enabled(trip)
        journalMessage = ""
        selected = sessions.selected
        qr = ""
        photos = emptyList()
        album = emptyList()
        title = ""
        members = ""
        actor = ""
        role = ""
        status = ""
        actorId = ""
    }

    fun refresh() {
        if (trip.isNotEmpty() && !busy) run { refreshData() }
    }

    private suspend fun refreshData() {
        val info =
            try {
                api.request(base, token)
            } catch (e: VehicleResponseError) {
                if (e.status == 401 || e.status == 404) {
                    sessions.leaveCurrent()
                    loadSavedState()
                    error("저장된 여행에 접근할 수 없습니다. 다른 여행을 열거나 새 여행을 시작하세요.")
                }
                throw e
            }
        val revision = info.getInt("revision")
        if (loadedRevision == revision) return
        val names = info.getJSONArray("members")
        val member = info.optString("memberId")
        val people = (0 until names.length()).map { names.getJSONObject(it) }
        val all = mutableListOf<GalleryPhoto>()
        var cursor = ""
        do {
            val page = api.request(base + "/photos?cursor=" + cursor, token)
            val rows = page.getJSONArray("items")
            for (i in 0 until rows.length()) {
                val p = rows.getJSONObject(i)
                all.add(
                    GalleryPhoto(
                        p.getString("id"),
                        p.getString("uploader"),
                        p.getInt("voteCount"),
                        p.getInt("myVote") != 0,
                    )
                )
            }
            cursor = if (page.isNull("nextCursor")) "" else page.getString("nextCursor")
        } while (cursor.isNotEmpty())
        val record = api.request(base + "/album", token)
        val ids = record.getJSONArray("orderedPhotoIds")
        album = (0 until ids.length()).map { ids.getString(it) }
        albumRevision = record.getInt("revision")
        title = info.getString("title")
        status = info.getString("state")
        if (status != "ACTIVE" && recording) toggleRecording()
        role = info.optString("role")
        members = people.joinToString { it.getString("nickname") }
        actorId = member
        actor = people.firstOrNull { it.getString("id") == member }?.getString("nickname") ?: ""
        val validSelection = restoredPhoto(selected, all)
        if (validSelection != selected) select(validSelection)
        photos = all
        loadedRevision = revision
    }

    fun showQr(kind: String) = run {
        if (kind == "") {
            qr = ""
            return@run
        }
        val origin = BuildConfig.WEB_ORIGIN.trimEnd('/')
        val uri = android.net.Uri.parse(origin)
        require(
            uri.scheme == "https" &&
                !uri.host.isNullOrEmpty() &&
                uri.host !in listOf("localhost", "127.0.0.1", "10.0.2.2")
        ) {
            "휴대폰용 HTTPS webOrigin 설정 필요"
        }
        val fragment =
            if (kind == "pair")
                "trip=" +
                    trip +
                    "&pair=" +
                    api.request(base + "/pair-code", token, "POST").getString("token")
            else "invite=" + sessions.code(kind)
        qr = origin + "/#" + fragment
    }

    fun select(id: String) {
        selected = id
        sessions.saveDetail(id)
    }

    private var actorId = ""

    fun vote(p: GalleryPhoto) = run {
        api.request(
            base + "/photos/" + p.id + "/vote",
            token,
            if (p.voted) "DELETE" else "PUT",
            expectedMember = actorId,
        )
        refreshData()
    }

    fun publish(ids: List<String>, revision: Int) = run {
        api.request(
            base + "/album",
            token,
            "PUT",
            JSONObject()
                .put("orderedPhotoIds", JSONArray(ids))
                .put("coverPhotoId", ids.first())
                .put("expectedRevision", revision),
        )
        refreshData()
    }
}
