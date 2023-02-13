import QtQuick
import QtQuick.Controls

Rectangle{
    width: parent.width
    height: parent.height*0.06
    color: "transparent"
    Text{
        text: "干燥机节能系统"
        color:'#00a7fe'
        font.pixelSize:parent.height*0.75
        font.bold:true
        anchors.horizontalCenter:parent.horizontalCenter
        anchors.top:parent.top
        anchors.topMargin:parent.height*0.2
    }
    Image{
        id:logo
        width:parent.width*0.1
        height:parent.height*0.8
        smooth:true
        anchors.left:parent.left
        anchors.leftMargin:parent.width*0.02
        anchors.top:parent.top
        anchors.topMargin:parent.height*0.35
        source:"../Source/Images/hansen.png"
    }
}
