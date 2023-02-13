import QtQuick
import QtQuick.Controls

Rectangle{
    width:parent.width
    height: parent.height/15
    color: "transparent"
    anchors.bottom: parent.bottom
    Text{
        anchors.right:parent.right
        anchors.rightMargin:parent.width*0.06
        anchors.top:parent.top
        color:'white'
        font.pixelSize: parent.height*0.6
        Timer {
            interval: 150
            running: true
            repeat: true
            onTriggered: {
                parent.text = Qt.formatDateTime(new Date(), "hh:mm:ss.zzz")
            }
        }
    }
    Button{
        anchors.right:parent.right
        anchors.rightMargin:10
        anchors.top:parent.top
        text: qsTr("下一页")
        onClicked: backend.next_page()
    }

}