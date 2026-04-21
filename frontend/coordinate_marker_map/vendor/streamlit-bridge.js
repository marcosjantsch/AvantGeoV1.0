const COMPONENT_READY = "streamlit:componentReady";
const SET_COMPONENT_VALUE = "streamlit:setComponentValue";
const SET_FRAME_HEIGHT = "streamlit:setFrameHeight";
const RENDER_EVENT = "streamlit:render";

class StreamlitBridge {
  static API_VERSION = 1;
  static RENDER_EVENT = RENDER_EVENT;
  static events = new EventTarget();
  static registeredMessageListener = false;
  static lastFrameHeight = undefined;

  static setComponentReady() {
    if (!StreamlitBridge.registeredMessageListener) {
      window.addEventListener("message", StreamlitBridge.onMessageEvent);
      StreamlitBridge.registeredMessageListener = true;
    }

    StreamlitBridge.sendBackMsg(COMPONENT_READY, {
      apiVersion: StreamlitBridge.API_VERSION,
    });
  }

  static setFrameHeight(height) {
    const resolvedHeight = height ?? document.body.scrollHeight;
    if (resolvedHeight === StreamlitBridge.lastFrameHeight) {
      return;
    }

    StreamlitBridge.lastFrameHeight = resolvedHeight;
    StreamlitBridge.sendBackMsg(SET_FRAME_HEIGHT, { height: resolvedHeight });
  }

  static setComponentValue(value) {
    StreamlitBridge.sendBackMsg(SET_COMPONENT_VALUE, {
      value,
      dataType: "json",
    });
  }

  static onMessageEvent(event) {
    const type = event.data?.type;
    if (type !== RENDER_EVENT) {
      return;
    }

    const args = event.data?.args ?? {};
    const disabled = Boolean(event.data?.disabled);
    const theme = event.data?.theme;
    const renderEvent = new CustomEvent(RENDER_EVENT, {
      detail: {
        args,
        disabled,
        theme,
      },
    });
    StreamlitBridge.events.dispatchEvent(renderEvent);
  }

  static sendBackMsg(type, data) {
    window.parent.postMessage(
      {
        isStreamlitMessage: true,
        type,
        ...data,
      },
      "*",
    );
  }
}

window.Streamlit = StreamlitBridge;
