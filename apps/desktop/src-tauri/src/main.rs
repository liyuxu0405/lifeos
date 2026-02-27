// LifeOS Tauri 层
// 职责：启动 Python 后端、系统托盘、全局快捷键、系统通知

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, TrayIconBuilder, TrayIconEvent},
    Manager, Runtime,
};

struct BackendProcess(Mutex<Option<Child>>);

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            Some(vec!["--autostart"]),
        ))
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            // 启动 Python 后端
            let backend = start_python_backend();
            if let Some(child) = backend {
                *app.state::<BackendProcess>().0.lock().unwrap() = Some(child);
            }

            // 系统托盘
            setup_tray(app)?;

            // macOS: 不在 Dock 显示（后台应用风格）
            #[cfg(target_os = "macos")]
            app.set_activation_policy(tauri::ActivationPolicy::Accessory);

            Ok(())
        })
        .on_window_event(|window, event| {
            // 关闭窗口时最小化到托盘，而不是退出
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                window.hide().unwrap();
                api.prevent_close();
            }
        })
        .invoke_handler(tauri::generate_handler![
            show_notification,
            get_backend_port,
        ])
        .run(tauri::generate_context!())
        .expect("LifeOS 启动失败");
}

fn start_python_backend() -> Option<Child> {
    // 生产环境：使用打包的 Python 可执行文件
    // 开发环境：使用系统 Python
    let backend_cmd = if cfg!(debug_assertions) {
        // 开发模式：从项目目录启动
        let manifest_dir = std::env::var("CARGO_MANIFEST_DIR")
            .unwrap_or_else(|_| ".".to_string());
        let backend_dir = std::path::Path::new(&manifest_dir)
            .parent()
            .unwrap()
            .parent()
            .unwrap()
            .join("backend");

        Command::new("python")
            .arg("main.py")
            .current_dir(backend_dir)
            .env("LIFEOS_PORT", "52700")
            .spawn()
    } else {
        // 生产模式：使用打包的二进制
        Command::new("lifeos-backend")
            .env("LIFEOS_PORT", "52700")
            .spawn()
    };

    match backend_cmd {
        Ok(child) => {
            println!("[Tauri] Python 后端已启动 (PID: {})", child.id());
            Some(child)
        }
        Err(e) => {
            eprintln!("[Tauri] Python 后端启动失败: {}", e);
            None
        }
    }
}

fn setup_tray<R: Runtime>(app: &tauri::App<R>) -> Result<(), Box<dyn std::error::Error>> {
    let show_item = MenuItem::with_id(app, "show", "打开 LifeOS", true, None::<&str>)?;
    let brief_item = MenuItem::with_id(app, "brief", "今日简报", true, None::<&str>)?;
    let quit_item = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;

    let menu = Menu::with_items(app, &[&show_item, &brief_item, &quit_item])?;

    let _tray = TrayIconBuilder::new()
        .menu(&menu)
        .tooltip("LifeOS")
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click { button: MouseButton::Left, .. } = event {
                let app = tray.app_handle();
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
        })
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            "quit" => {
                // 关闭 Python 后端进程
                if let Some(mut child) = app
                    .state::<BackendProcess>()
                    .0
                    .lock()
                    .unwrap()
                    .take()
                {
                    let _ = child.kill();
                }
                app.exit(0);
            }
            _ => {}
        })
        .build(app)?;

    Ok(())
}

#[tauri::command]
fn show_notification(title: String, body: String, app: tauri::AppHandle) {
    use tauri_plugin_notification::NotificationExt;
    let _ = app.notification()
        .builder()
        .title(&title)
        .body(&body)
        .show();
}

#[tauri::command]
fn get_backend_port() -> u16 {
    52700
}
