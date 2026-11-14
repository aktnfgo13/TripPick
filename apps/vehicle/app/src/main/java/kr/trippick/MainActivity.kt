@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

package kr.trippick

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay

class MainActivity : ComponentActivity() {
    private val travel: TravelModel by viewModels()
    private var foreground by mutableStateOf(false)
    private var navStatus by mutableStateOf("내비 미연결")
    private var allowed by mutableStateOf(false)
    private var gate: SafetyGate? = null
    private var probe: SdkProbe? = null

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        probe = runCatching { SdkProbe(applicationContext) }.getOrNull()
        setContent {
            DisposableEffect(foreground, travel.trip, travel.recording) {
                val trip = travel.trip
                val navigation =
                    if (foreground && travel.recording && trip.isNotBlank())
                        runCatching {
                                NavigationAdapter(
                                        this@MainActivity,
                                        { navStatus = it },
                                        { event ->
                                            if (
                                                foreground &&
                                                    travel.trip == trip &&
                                                    travel.recording
                                            )
                                                travel.observe(event)
                                        },
                                    )
                                    .also { it.start() }
                            }
                            .onFailure { navStatus = "내비 시작 실패" }
                            .getOrNull()
                    else null
                if (!travel.recording) navStatus = "자동 기록 꺼짐"
                onDispose { runCatching { navigation?.close() } }
            }
            MaterialTheme(colors = lightColors(primary = androidx.compose.ui.graphics.Color(0xff165b50), secondary = androidx.compose.ui.graphics.Color(0xff316968))) {
                if (allowed) VehicleRoom(travel, navStatus)
                else Box(Modifier.padding(32.dp)) { Text("TripPick · 주차 및 화면 사용 허용 상태를 기다립니다.") }
            }
        }
    }

    override fun onStart() {
        super.onStart()
        foreground = true
        gate = SafetyGate(this) { allowed = it }
    }

    override fun onStop() {
        foreground = false
        gate?.close()
        gate = null
        allowed = false
        super.onStop()
    }

    override fun onDestroy() {
        probe?.close()
        super.onDestroy()
    }
}

@Composable
fun VehicleRoom(model: TravelModel, navStatus: String) {
    var name by remember { mutableStateOf("") }
    val preferences =
        androidx.compose.ui.platform.LocalContext.current.getSharedPreferences("journal-view", 0)
    var mapOpen by
        remember(model.trip) { mutableStateOf(preferences.getBoolean("open/" + model.trip, false)) }
    fun openMap(value: Boolean) {
        mapOpen = value
        preferences.edit().putBoolean("open/" + model.trip, value).apply()
    }
    var creating by remember { mutableStateOf(false) }
    LaunchedEffect(model.trip) {
        while (true) {
            model.refresh()
            delay(4000)
        }
    }
    if (mapOpen) {
        JournalMap(model) { openMap(false) }
        return
    }
    if (model.qr.isNotBlank()) {
        androidx.activity.compose.BackHandler { model.showQr("") }
        Column(Modifier.fillMaxSize().padding(16.dp), horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
            Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Text(model.title, Modifier.weight(1f), style = MaterialTheme.typography.h6, maxLines = 1)
                Button(onClick = { model.showQr("") }) { Text("QR 닫기") }
            }
            val instruction = when (model.qrKind) {
                "claim" -> "관리자 휴대폰으로만 스캔하세요"
                "pair" -> "참여한 휴대폰으로 차량 계정을 연결하세요"
                else -> "휴대폰으로 스캔하여 참여하세요"
            }
            Text(instruction)
            InviteQr(model.qr, Modifier.weight(1f).fillMaxWidth())
            Text("참여자 ${model.memberCount}명 · " + if (model.error.isEmpty()) "최근 조회 정상" else "연결 확인 필요")
            Text(model.qr, style = MaterialTheme.typography.caption)
            if (model.qrKind == "invite") Text("참여 코드 " + model.qr.substringAfter("#invite="))
        }
        return
    }
    Column(Modifier.fillMaxSize().padding(14.dp)) {
        Text(navStatus, style = MaterialTheme.typography.caption)
        if (model.error.isNotBlank()) Text(model.error, color = MaterialTheme.colors.error)
        Box(Modifier.height(4.dp)) { if (model.busy) LinearProgressIndicator() }
        if (model.trip.isBlank() || creating) {
            Text("TripPick", style = MaterialTheme.typography.h4)
            TextButton(onClick = { openMap(true) }) { Text("전국 지도 둘러보기") }
            Text("새 여행 시작", style = MaterialTheme.typography.h6)
            OutlinedTextField(name, { name = it }, label = { Text("여행 제목") }, singleLine = true)
            Button(
                onClick = {
                    creating = false
                    model.create(name)
                },
                enabled = name.isNotBlank() && !model.busy,
            ) {
                Text("여행 생성")
            }
            Column(Modifier.verticalScroll(rememberScrollState())) {
                if (creating) TextButton(onClick = { creating = false }) { Text("기존 여행") }
                for ((id, label) in model.savedTrips) {
                    TextButton(
                        onClick = {
                            creating = false
                            model.reopen(id)
                        }
                    ) {
                        Text("다시 열기 · " + label)
                    }
                }
            }
        } else {
            Text(
                model.title + " · " + model.status + " · 사진 " + model.photos.size + "장",
                style = MaterialTheme.typography.h6,
            )
            Text("참여자 ${model.memberCount}명 · " + model.members + " · 차량 계정 " + model.actor.ifBlank { "미연결" })
            if (model.status == "ACTIVE")
                TextButton(onClick = { model.toggleRecording() }) {
                    Text(if (model.recording) "자동 기록 중단" else "자동 기록 시작")
                }
            Text("여행 ID " + model.trip, style = MaterialTheme.typography.caption)
            if (model.journalMessage.isNotEmpty()) Text(model.journalMessage)

            FlowRow {
                Button(onClick = { model.showQr("invite") }, enabled = !model.busy) { Text("참여 QR") }
                if (model.status == "DRAFT")
                    TextButton(onClick = { model.showQr("claim") }) { Text("소유권 QR") }
                TextButton(onClick = { model.showQr("pair") }) { Text("계정 연결") }
                TextButton(onClick = { openMap(!mapOpen) }) {
                    Text(if (mapOpen) "지도 닫기" else "여행 지도")
                }
                TextButton(onClick = { model.refresh() }) { Text("새로고침") }
                TextButton(onClick = { creating = true }) { Text("새 여행") }
            }
            Gallery(model)
        }
    }
}
