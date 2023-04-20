import QtQuick
import QtQuick.Controls

Rectangle{
    id: detail_rect
    width: parent.width / gridAll.columns - 1
    height: parent.height / gridAll.rows - 1
    property var font_size: height / 24
    Text{
        id: code_text
        anchors.top:parent.top
        text: modelData.id + ":" + modelData.code + "-" + modelData.switch_count
            + (modelData.auto_control?" auto" : " manual")
        color: modelData.auto_control ? "blue" : "black"
        font.pixelSize: font_size * 1.2
    }
    Text{
        id: status_text
        anchors.top: code_text.bottom
        text: "run:" + modelData.run_status + " rid:" + modelData.real_id
        color: modelData.run_status == 1 ? "green" : "red"
        font.pixelSize: font_size
    }
    Text{
        id: a_working_text
        anchors.top: status_text.bottom
        text: (modelData.a_working ? "A燥B生-" : "B燥A生-") + modelData.a_working2
            + " step:" + modelData.step + " 电流:" + modelData.heater_power
        font.pixelSize: font_size
    }
    Text{
        id: elapse_text
        anchors.top:a_working_text.bottom
        text: "elps:" + modelData.elapse_text + " pre:" + modelData.elapse_prev
            + " mnt:" + (modelData.step_seconds/60).toFixed(1)
        font.pixelSize: font_size
    }
    Text{
        id: dew_temp_sum
        anchors.top:elapse_text.bottom
        text: "temp:" + modelData.dew_temp_sum
        font.pixelSize: font_size
    }
    Text{
        id: dew_point_text
        anchors.top:dew_temp_sum.bottom
        text: "dew:" + modelData.dew_point + ",lvl:" + modelData.regen_level.toFixed(1)
        font.pixelSize: font_size
    }
    Text{
        id: a_dew_sum
        anchors.top:dew_point_text.bottom
        text: "a_dew:" + modelData.a_dew_sum
        font.pixelSize: font_size
    }
    Text{
        id: b_dew_sum
        anchors.top:a_dew_sum.bottom
        text: "b_dew:" + modelData.b_dew_sum
        font.pixelSize: font_size
    }
    Text{
        id: regen_id_text
        anchors.top:b_dew_sum.bottom
        text: "regen begin:" + modelData.regen_begin_id + ",end:" + modelData.regen_end_id
        font.pixelSize: font_size
    }
    Text{
        id: a_heat1_text
        anchors.top:regen_id_text.bottom
        text: "a.heat lvl:" + modelData.a_dew_level.toFixed(1) + ",dew:" + modelData.a_dew_point.toFixed(1)
        font.pixelSize: font_size
    }
    Text{
        id: a_heat2_text
        anchors.top:a_heat1_text.bottom
        text: "reduce:" + modelData.a_reduce + ",bg:" + modelData.a_begin_id + ",nd:" + modelData.a_end_id
        font.pixelSize: font_size
    }
    Text{
        id: b_heat1_text
        anchors.top:a_heat2_text.bottom
        text: "b.heat lvl:" + modelData.b_dew_level.toFixed(1) + ",dew:" + modelData.b_dew_point.toFixed(1)
        font.pixelSize: font_size
    }
    Text{
        id: b_heat2_text
        anchors.top:b_heat1_text.bottom
        text: "reduce:" + modelData.b_reduce + ",bg:" + modelData.b_begin_id + ",nd:" + modelData.b_end_id
        font.pixelSize: font_size
    }
    Text{
        id: accumulate_text
        anchors.top:b_heat2_text.bottom
        text: "pw:" + modelData.accumulate_power + ",hr:" + modelData.accumulate_elapse.toFixed(1) +
            ",rt:" + modelData.accumulate_rate.toFixed(2)
        font.pixelSize: font_size
    }
    Text{
        id: heat_temp_text
        anchors.top:accumulate_text.bottom
        text: "heat_t:" + modelData.heat_out_t + ",dry_t:" + modelData.dryer_out_t
        font.pixelSize: font_size
    }
}
