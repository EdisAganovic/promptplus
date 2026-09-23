!ifndef BUILD_UNINSTALLER
  !include nsDialogs.nsh
  !include WinMessages.nsh

Var desktopShortcutCheckbox
Var desktopShortcutState

!macro customWelcomePage
  PageEx custom
    PageCallbacks desktopShortcutPageCreate desktopShortcutPageLeave
  PageExEnd
!macroend

Function desktopShortcutPageCreate
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 24u "PromptPlus ${VERSION} will be installed on your computer."
  Pop $0
  ${NSD_CreateCheckbox} 0 34u 100% 12u "Create a desktop shortcut"
  Pop $desktopShortcutCheckbox
  ${NSD_Check} $desktopShortcutCheckbox
  nsDialogs::Show
FunctionEnd

Function desktopShortcutPageLeave
  ${NSD_GetState} $desktopShortcutCheckbox $desktopShortcutState
FunctionEnd

!macro customInstall
  ${If} $desktopShortcutState == ${BST_CHECKED}
    CreateShortCut "$DESKTOP\${SHORTCUT_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE_FILENAME}" "" "$INSTDIR\${APP_EXECUTABLE_FILENAME}" 0
    WinShell::SetLnkAUMI "$DESKTOP\${SHORTCUT_NAME}.lnk" "${APP_ID}"
  ${EndIf}
!macroend
!endif
