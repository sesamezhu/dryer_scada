import QtQuick
import QtQuick.Window
import QtQuick.Controls

Window{
    id:top_window
    width: Screen.width
    height: Screen.height
    title: "Dryer SCADA"
    flags: Qt.Window // | Qt.FramelessWindowHint
    visible: true
    visibility: "Maximized"

    Component.onCompleted: {
        console.log("Component.onCompleted")
        backend.start_threads()
    }
    onClosing: {
        console.log("onClosing")
        backend.stop_threads()
    }
    
    Shortcut {
        sequence: "Ctrl+Q"    //退出当前窗口，以及停止线程
        onActivated: {
            top_window.close()
        }
    }

    Image{
        id: bg
        fillMode: Image.Stretch
        width:parent.width
        height:parent.height
        anchors.centerIn: parent
        smooth: true
        source: '../Source/Images/bg.png'
        Header{}
        Grid{
            id:gridAll
            rows: backend.grid_rows
            columns: backend.grid_columns
            spacing: 2
            anchors.left:parent.left
            anchors.leftMargin:bg.width*0.025
            anchors.top:parent.top
            anchors.topMargin:bg.height*0.07
            width: parent.width - anchors.leftMargin * 2
            height: parent.height - anchors.topMargin * 2
            flow: Grid.LeftToRight
            Repeater{
                id:repeater
                model:backend.detail_models
                DetailRect{}
            }
        }
        Footer{}
    }
}
