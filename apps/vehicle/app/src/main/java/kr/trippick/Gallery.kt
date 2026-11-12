package kr.trippick

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.*
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

fun canVote(actor:String,busy:Boolean)=actor.isNotBlank() && !busy

@Composable fun Gallery(model:TravelModel){
    var albumOnly by remember(model.trip){mutableStateOf(false)}
    var editing by remember(model.trip){mutableStateOf(false)}
    var revision by remember {mutableIntStateOf(0)}
    var picks by remember {mutableStateOf(listOf<String>())}
    val detail=model.photos.firstOrNull{it.id==model.selected}
    if(detail!=null){
        Row{
            Button(onClick={model.select("")}){Text("목록")}
            TextButton(onClick={model.vote(detail)},enabled=canVote(model.actor,model.busy)){
                Text((if(detail.voted)"좋아요 취소 " else "좋아요 ")+detail.count)
            }
            Text(detail.uploader)
        }
        Preview(model,detail.id,Modifier.fillMaxSize())
        return
    }
    Row{
        TextButton(onClick={albumOnly=false}){Text("전체 사진")}
        TextButton(onClick={albumOnly=true}){Text("공유 앨범")}
        if(model.role=="owner")TextButton(onClick={
            editing=!editing;albumOnly=false;revision=model.albumRevision
            picks=model.album.ifEmpty{model.photos.filter{it.count>0}.map{it.id}}
        }){Text(if(editing)"편집 취소" else "최종 선정")}
        if(editing)Button(onClick={model.publish(picks,revision);editing=false},enabled=picks.isNotEmpty()){Text("앨범 확정")}
    }
    val lookup=remember(model.photos){model.photos.associateBy{it.id}}
    val photos=if(albumOnly)model.album.mapNotNull(lookup::get) else model.photos
    if(photos.isEmpty())Text(if(albumOnly)"확정한 앨범이 없습니다." else "업로드된 사진이 없습니다.")
    LazyVerticalGrid(GridCells.Adaptive(160.dp)){
        items(photos,key={it.id}){p->
            Column(Modifier.padding(5.dp).clickable{
                if(editing)picks=if(p.id in picks)picks-p.id else picks+p.id
                else model.select(p.id)
            }){
                Preview(model,p.id,Modifier.fillMaxWidth().height(110.dp))
                Text(p.uploader+" · 좋아요 "+p.count+if(editing && p.id in picks)" · 선정" else "")
            }
        }
    }
}
