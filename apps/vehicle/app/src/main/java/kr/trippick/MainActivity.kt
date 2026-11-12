package kr.trippick

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.delay

class MainActivity:ComponentActivity(){
    private var allowed by mutableStateOf(false)
    private var gate:SafetyGate?=null
    private var probe:SdkProbe?=null
    override fun onCreate(state:Bundle?){
        super.onCreate(state)
        probe=runCatching { SdkProbe(applicationContext) }.getOrNull()
        setContent { MaterialTheme {
            if(allowed) VehicleRoom(viewModel())
            else Box(Modifier.padding(32.dp)){Text("TripPick · 주차 및 화면 사용 허용 상태를 기다립니다.")}
        }}
    }
    override fun onStart(){super.onStart();gate=SafetyGate(this){allowed=it}}
    override fun onStop(){gate?.close();gate=null;allowed=false;super.onStop()}
    override fun onDestroy(){probe?.close();super.onDestroy()}
}

@Composable fun VehicleRoom(model:TravelModel){
    var name by remember {mutableStateOf("")}
    var creating by remember {mutableStateOf(false)}
    LaunchedEffect(model.trip){while(true){model.refresh();delay(4000)}}
    Column(Modifier.fillMaxSize().padding(14.dp)){
        if(model.error.isNotBlank())Text(model.error,color=MaterialTheme.colors.error)
        if(model.busy) LinearProgressIndicator()
        if(model.trip.isBlank()||creating){
            Text("TripPick",style=MaterialTheme.typography.h4)
            OutlinedTextField(name,{name=it},label={Text("여행 제목")},singleLine=true)
            Button(onClick={creating=false;model.create(name)},enabled=name.isNotBlank()&&!model.busy){Text("여행 생성")}
            if(creating)TextButton(onClick={creating=false}){Text("기존 여행")}
        }else{
            Text(model.title+" · "+model.status+" · 사진 "+model.photos.size+"장",style=MaterialTheme.typography.h6)
            Text("참여자 "+model.members+" · 차량 계정 "+model.actor.ifBlank{"미연결"})
            Text("여행 ID "+model.trip,style=MaterialTheme.typography.caption)
            Row{
                TextButton(onClick={model.showQr("invite")}){Text("참여 QR")}
                if(model.status=="DRAFT")TextButton(onClick={model.showQr("claim")}){Text("소유권 QR")}
                TextButton(onClick={model.showQr("pair")}){Text("계정 연결")}
                TextButton(onClick={model.refresh()}){Text("새로고침")}
                TextButton(onClick={creating=true}){Text("새 여행")}
            }
            if(model.qr.isNotBlank()){
                Button(onClick={model.showQr("")}){Text("QR 닫기")}
                InviteQr(model.qr,Modifier.fillMaxHeight().aspectRatio(1f))
            }else Gallery(model)
        }
    }
}
