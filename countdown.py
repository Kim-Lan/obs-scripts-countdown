import obspython as obs

# Constants
SOURCE_NAME = "source"
FINISHED_NAME = "finished"
DURATION_HOUR_NAME = "duration_hour"
DURATION_MIN_NAME = "duration_min"
DURATION_SEC_NAME = "duration_sec"
AUTOSTART_NAME = "autostart"
START_BUTTON_NAME = "start_button"
RESET_BUTTON_NAME = "reset_button"

source_name = ""
file_path = ""
total_seconds = 0
current_seconds = 0
previous_text = ""
finished_text = ""
show_hours = False
active = False

def script_description():
    return "countdown timer"

def script_load(settings):
    sh = obs.obs_get_signal_handler()
    obs.obs_frontend_add_event_callback(on_frontend_event)
    obs.signal_handler_connect(sh, "source_deactivate", source_deactivated)

def on_frontend_event(event):
    if event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTED or event == obs.OBS_FRONTEND_EVENT_RECORDING_STARTED:
        if autostart:
            start_countdown()
    elif event == obs.OBS_FRONTEND_EVENT_STREAMING_STOPPED or event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        reset()

def script_update(settings):
    global source_name
    global finished_text
    global total_seconds
    global autostart
    global show_hours

    source_name = obs.obs_data_get_string(settings, SOURCE_NAME)
    finished_text = obs.obs_data_get_string(settings, FINISHED_NAME)
    hours = obs.obs_data_get_int(settings, DURATION_HOUR_NAME)
    minutes = obs.obs_data_get_int(settings, DURATION_MIN_NAME)
    seconds = obs.obs_data_get_int(settings, DURATION_SEC_NAME)
    total_seconds = (hours * 60 + minutes) * 60 + seconds
    autostart = obs.obs_data_get_bool(settings, AUTOSTART_NAME)

    if hours > 0:
        show_hours = True
    else:
        show_hours = False

def counting_down():
    global current_seconds

    if current_seconds > 0:
        current_seconds -= 1
    else:
        obs.remove_current_callback()
    update_time()

def update_time():
    global current_seconds
    global finished_text
    global previous_text

    seconds = current_seconds % 60
    total_minutes = current_seconds // 60
    minutes = total_minutes % 60
    hours = total_minutes // 60
    text = ""

    if show_hours:
        text = '{:02d}:'.format(hours)
    text += '{:02d}:{:02d}'.format(minutes, seconds)

    if current_seconds < 1:
        text = finished_text
        end_countdown()

    if text != previous_text:
        previous_text = text
        set_text(text)

def start_countdown():
    global active
    global current_seconds

    if not active:
        current_seconds = total_seconds
        update_time()
        obs.timer_add(counting_down, 1000)
        active = True

def end_countdown():
    global active
    active = False
    obs.timer_remove(counting_down)

def reset():
    global active
    global current_seconds

    current_seconds = total_seconds
    active = False
    update_time()
    obs.timer_remove(counting_down)

def start_button_clicked(props, prop):
    start_countdown()

def reset_button_clicked(props, prop):
    reset()

def source_deactivated(calldata):
    if match_source(calldata):
        reset()

def match_source(calldata):
    source = obs.calldata_source(calldata, "source")
    if source is not None:
        name = obs.obs_source_get_name(source)
        return name == source_name
    return False

def set_text(text: str):
    source = obs.obs_get_source_by_name(source_name)
    if source is not None:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)

def script_defaults(settings):
    obs.obs_data_set_default_int(settings, DURATION_HOUR_NAME, 0)
    obs.obs_data_set_default_int(settings, DURATION_MIN_NAME, 3)
    obs.obs_data_set_default_int(settings, DURATION_SEC_NAME, 0)
    obs.obs_data_set_default_string(settings, FINISHED_NAME, "starting soon")
    obs.obs_data_set_default_bool(settings, AUTOSTART_NAME, True)

def source_select(props, sources, prop_name: str, label: str):
    p = obs.obs_properties_add_list(props, prop_name, label,
                                    obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

def script_properties():
    props = obs.obs_properties_create()

    sources = obs.obs_enum_sources()
    source_select(props, sources, SOURCE_NAME, "Source")
    obs.obs_properties_add_text(props, FINISHED_NAME, "Text when Finished", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, DURATION_HOUR_NAME, "Hours", 0, 200, 1)
    obs.obs_properties_add_int(props, DURATION_MIN_NAME, "Minutes", 0, 59, 1)
    obs.obs_properties_add_int(props, DURATION_SEC_NAME, "Seconds", 0, 59, 1)
    obs.obs_properties_add_bool(props, AUTOSTART_NAME, "Start automatically with stream start?")
    obs.obs_properties_add_button(props, START_BUTTON_NAME, "Start", start_button_clicked)
    obs.obs_properties_add_button(props, RESET_BUTTON_NAME, "Reset", reset_button_clicked)
    obs.source_list_release(sources)

    return props

def script_unload():
    reset()
    obs.obs_frontend_remove_event_callback(on_frontend_event)
