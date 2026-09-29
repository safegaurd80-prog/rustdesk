# res/updesk_patch.py — UP-Desk 빌드 패치(빌드 러너에서 1회 실행). 값은 환경변수로만 받는다. 이 파일에 값 없음.
import os, pathlib
host = os.environ["UPDESK_RELAY_HOST"].strip()
key  = os.environ["UPDESK_PUB_KEY"].strip()
assert host and key and '"' not in host + key, "UPDESK_RELAY_HOST / UPDESK_PUB_KEY 비었거나 따옴표 포함"

def edit(path, pairs):
    p = pathlib.Path(path); s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        c = s.count(old)
        assert c == 1, f"{path}: 기대 문자열이 {c}회 발견됨(원본이 바뀐 듯) → {old[:60]!r}"
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8"); print("patched", path, len(pairs))

# ① 서버 주소·공개키·앱 이름 상수 — 공개 릴레이(rs-ny.rustdesk.com) 자체가 바이너리에서 사라진다
edit("libs/hbb_common/src/config.rs", [
    ('pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
     f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{host}"];'),
    ('pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
     f'pub const RS_PUB_KEY: &str = "{key}";'),
    ('RwLock::new("RustDesk".to_owned())', 'RwLock::new("UP-Desk".to_owned())'),
])

# ② 정책 강제 — 프로세스 시작 직후 load_custom_client() 첫 줄에 박는다(core_main.rs:36 에서 호출됨)
BLOCK = '''pub fn load_custom_client() {
    // ── UP-Desk 고정(빌드 시 박힘 · 사용자 변경 불가): 우리 릴레이만 · 1회용 코드만 · 수신 전용 · 설정화면 숨김
    {
        let host = "__H__";
        let key = "__K__";
        let fixed = [
            ("custom-rendezvous-server", host), ("relay-server", host), ("key", key),
            ("approve-mode", "password"),                       // 승인 = 비밀번호로만
            ("verification-method", "use-temporary-password"),  // 비밀번호 = 1회용(임시)만 → 고정 비번 기능 자체 OFF
            ("allow-remote-config-modification", "N"),          // 원격에서 설정 변경 금지
            ("direct-server", "N"),                             // 직접 IP 접속 OFF
            ("enable-lan-discovery", "N"),                      // LAN 탐색 OFF
            ("enable-check-update", "N"),                       // 공식 업데이트 확인 OFF(우리 배포본이 덮이면 안 됨)
        ];
        let mut o = config::OVERWRITE_SETTINGS.write().unwrap();
        let mut l = config::OVERWRITE_LOCAL_SETTINGS.write().unwrap();
        for (k, v) in fixed {
            o.insert(k.to_owned(), v.to_owned());
            l.insert(k.to_owned(), v.to_owned());
        }
        drop(o);
        drop(l);
        let mut h = config::HARD_SETTINGS.write().unwrap();
        for (k, v) in [("conn-type", "incoming"), ("disable-settings", "Y"), ("disable-account", "Y")] {
            h.insert(k.to_owned(), v.to_owned());
        }
    }
'''.replace("__H__", host).replace("__K__", key)
edit("src/common.rs", [("pub fn load_custom_client() {\n", BLOCK)])

# ③ 윈도우 파일 속성(우클릭 → 속성 → 자세히) — ASCII 만 쓴다(.rc 인코딩 안전)
edit("flutter/windows/runner/Runner.rc", [
    ('VALUE "FileDescription", "RustDesk Remote Desktop" "\\0"', 'VALUE "FileDescription", "UP-Desk Remote Support" "\\0"'),
    ('VALUE "InternalName", "rustdesk" "\\0"',                   'VALUE "InternalName", "UP-Desk" "\\0"'),
    ('VALUE "OriginalFilename", "rustdesk.exe" "\\0"',           'VALUE "OriginalFilename", "UP-Desk.exe" "\\0"'),
    ('VALUE "ProductName", "RustDesk" "\\0"',                    'VALUE "ProductName", "UP-Desk" "\\0"'),
])
print("UP-Desk patch OK")
