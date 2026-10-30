# Windows 11 — بيئة التطوير المحلية (Environment B)

| الحقل | القيمة |
|---|---|
| القرار | [ADR-0008](../architecture/adr/0008-multi-environment-hosting-railway-windows-ubuntu.md)؛ **D4 معتمد** في [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) (2026-10-18) |
| المسار المعتمد | **Ubuntu داخل WSL2 + Docker Engine + Docker Compose plugin** (المسار الوحيد المدعوم) |
| الحالة | الحزمة (Compose local) `Tested (cloud session)` على Linux؛ **التشغيل على Windows 11 حقيقي NOT RUN** — [#17](https://github.com/faenazi/ef-ai-workspace/issues/17) |
| العنوان | `http://localhost:3080`، ولوحة الإدارة `http://localhost:3000` ([ADR-0016](../architecture/adr/0016-librechat-admin-panel.md)) — على واجهة loopback فقط، غير مكشوفين للشبكة |
| البيانات | اصطناعية فقط |

لا يُثبَّت MongoDB ولا LibreChat على Windows مباشرة: كل شيء حاويات Linux.

## 1. بيئة تشغيل الحاويات (D4)

| الخيار | الحالة | الترخيص |
|---|---|---|
| **Docker Engine داخل Ubuntu WSL2** (§2) | **المعتمد والوحيد المدعوم** | Docker Engine (Moby) مفتوح المصدر |
| Rancher Desktop / Podman Desktop | غير مُختبرين | مفتوحا المصدر |

Docker Desktop **غير مدعوم في هذا المستودع**: يتطلب اشتراكاً مدفوعاً للجهات الحكومية
([Docker docs](https://docs.docker.com/subscription-billing/desktop-license/)، تحقق 2026-10-18)، ومساعد PowerShell الذي كان
يخدمه أُزيل بقرار المالك في 2026-10-20 ([#75](https://github.com/faenazi/ef-ai-workspace/issues/75)). كل الأوامر تُنفَّذ داخل
طرفية Ubuntu في WSL2. وصف لشروط منشورة وليس رأياً قانونياً؛ الامتثال قرار المالك/المشتريات.

## 2. المسار المعتمد: Ubuntu داخل WSL2 + Docker Engine

**المتطلبات:** Windows 11، و8 GB RAM على الأقل متاحة لـ WSL، و≥ 15 GB قرص (الصور ~6 GB).

**أ) WSL2 وUbuntu** — PowerShell **كمسؤول**، ثم إعادة التشغيل وإنشاء مستخدم Linux عند أول فتح لـ Ubuntu:

```powershell
wsl --install -d Ubuntu-24.04
```

**ب) Docker Engine وCompose plugin** — داخل طرفية Ubuntu (المستودع الرسمي لـ Docker، [docs.docker.com/engine/install/ubuntu](https://docs.docker.com/engine/install/ubuntu/)):

```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl git openssl python3
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"     # ثم أغلق طرفية Ubuntu وافتحها من جديد
docker compose version              # يجب 2.24 أو أحدث
```

إن لم يعمل `docker` بعد إعادة الفتح: `sudo service docker start` (أو فعّل systemd في `/etc/wsl.conf`: `[boot]` ثم `systemd=true`، ثم `wsl --shutdown`).
عضوية مجموعة `docker` تعادل صلاحيات root داخل WSL — لمستخدم المطوّر فقط.

**ج) التشغيل** — استنسخ داخل نظام ملفات WSL (`~/src`)، **لا** تحت `/mnt/c` (الأداء والصلاحيات):

```bash
mkdir -p ~/src && cd ~/src
git clone https://github.com/faenazi/ef-ai-workspace.git && cd ef-ai-workspace
scripts/setup/new-env.sh local                                   # .env بأسرار جديدة (mode 600، لا تُطبع)
cd infrastructure/compose
alias efc='docker compose -f compose.yaml -f compose.local.yaml'
efc up -d && efc ps                                              # الخدمات الأربع healthy (أول مرة: تنزيل ~7.5 GB)
efc exec librechat npm run create-user -- admin@example.invalid "Platform Admin" admin --email-verified=true
```

افتح `http://localhost:3080` من متصفح Windows (WSL2 يمرر `localhost` افتراضياً)، ولوحة الإدارة على `http://localhost:3000`
بالحساب نفسه ([runbook.md §6](runbook.md#6-لوحة-الإدارة-admin-panel--adr-0016)).

**`.env` أُنشئ قبل لوحة الإدارة (#141):** `docker compose` يرفض البدء حتى تُضاف القيمتان، مرة واحدة من `infrastructure/compose`:
`printf 'ADMIN_PANEL_URL=http://localhost:3000\nADMIN_PANEL_SESSION_SECRET=%s\n' "$(openssl rand -hex 32)" >> .env`.

**`.env` أُنشئ قبل البحث في المحادثات (#125):** `docker compose` يرفض البدء حتى يُضاف المفتاح، مرة واحدة:
`echo "MEILI_MASTER_KEY=$(openssl rand -hex 32)" >> .env` من `infrastructure/compose`.

| المهمة | الأمر (من `infrastructure/compose` داخل WSL) |
|---|---|
| إيقاف / تشغيل (البيانات تبقى) | `efc down` / `efc up -d` |
| السجلات | `efc logs --tail 200 librechat` |
| نسخ احتياطي | `../../scripts/operations/backup.sh $(efc ps -q mongodb) $(efc ps -q librechat) ~/efaiw-backups` |
| استعادة (مُدمّر) | `../../scripts/operations/restore.sh $(efc ps -q mongodb) $(efc ps -q librechat) ~/efaiw-backups/<timestamp>` (يعيد تشغيل librechat ويعيد بناء فهرس البحث) |
| إعادة ضبط (**يحذف كل البيانات المحلية**) | `efc down -v` |

نفس الحزمة والسكربتات مُختبرة في جلسة السحابة (Linux): `compose-stack.sh local` 41/41 بما فيها النسخ والاستعادة. **على WSL2 حقيقي: NOT RUN (#17).**

## 3. الأمان المحلي

- المنفذ مربوط بـ `127.0.0.1` فقط (مفروض بـ `compose_checks.py`، مُختبر T21)؛ MongoDB بلا منفذ على شبكة internal.
- `.env` والنسخ الاحتياطية تحتوي أسراراً/محادثات: لا تشاركها ولا تنسخها لبيئة أخرى؛ `backups/` و`.env` مُتجاهلان في Git.
- نفس الإعداد المشترك (`infrastructure/common/`) المستخدم في Railway وUbuntu؛ التسجيل الذاتي مغلق (ADR-0024)، فالحسابات ينشئها المسؤول بـ `create-user`.

## 4. استكشاف الأخطاء

| العَرَض | الحل |
|---|---|
| `Cannot connect to the Docker daemon` | `sudo service docker start` داخل WSL |
| `Docker Compose … too old` | حدّث `docker-compose-plugin` إلى 2.24+ |
| `localhost:3080` لا يفتح من Windows | `wsl --shutdown` ثم أعد التشغيل؛ تحقق من `efc ps` |
| المنفذ 3080 مستخدم | `.env` جديد بـ `new-env.sh local --port 3081` بعد نقل القديم |
| المنفذ 3000 مستخدم | `.env` جديد بـ `new-env.sh local --admin-port 3001`، أو عدّل `LOCAL_ADMIN_PORT` و`ADMIN_PANEL_URL` معاً |
| الملفات بنهايات CRLF | لا تعطّل `.gitattributes`؛ أعد الاستنساخ داخل WSL |
