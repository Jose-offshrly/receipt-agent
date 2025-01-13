import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"
import React, { useCallback, useEffect, useMemo, useState, ReactElement } from "react"
import './App.css';  // Import your CSS file

function SurveyOptions({ args, disabled, theme }: ComponentProps): ReactElement {

  const [active, setActive] = useState("")

  function handle_click(value: string) {

    if (value === active) return;

    setActive(value)
    Streamlit.setComponentValue(value)
  }

  useEffect(() => {
    Streamlit.setFrameHeight()
  }, [theme])


  return (
    <div className="btn-container">
      <button onClick={() => handle_click("Very Satisfied")}>Very Satisfied</button>
      <button onClick={() => handle_click("Satisfied")}>Satisfied</button>
      <button onClick={() => handle_click("Neutral")}>Neutral</button>
      <button onClick={() => handle_click("Dissatisfied")}>Dissatisfied</button>
      <button onClick={() => handle_click("Very Dissatisfied")}>Very Dissatisfied</button>
      </div>
  )
}

export default withStreamlitConnection(SurveyOptions)
