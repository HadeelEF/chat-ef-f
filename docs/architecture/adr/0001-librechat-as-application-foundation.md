# ADR-0001 — LibreChat أساساً للتطبيق (LibreChat as Application Foundation)

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-17 |
| Deciders | مالك المشروع (ميثاق `CLAUDE.md` commit `11e80e2` + موجّه M0) |
| Related | FR-002…FR-012, ADR-0006 |

## Context

نحتاج منصّة محادثة ذكاء اصطناعي مؤسسية تدعم مزوّدين متعددين، نماذج محلية، وكلاء، مهارات، RAG، MCP،
Artifacts، OIDC، وواجهة عربية — دون بناء كل ذلك من الصفر.

## Decision

اعتماد [LibreChat](https://github.com/LibreChat-AI/LibreChat) (ترخيص MIT) أساساً للتطبيق، باستخدام الحاويات الرسمية
والإعداد المدعوم (`.env` + `librechat.yaml`). خط الأساس المرجعي عند كتابة هذا القرار: **v0.8.8** (tag بتاريخ 2026-09-30،
`librechat.yaml` config version `1.3.17`). تثبيت الإصدار الفعلي (tag + digest) يتم في M1.

## Rationale

قدرات متحقق منها في المصدر الرسمي v0.8.8 (التفاصيل والأدلة في [overview.md](../overview.md#3-قدرات-librechat-v088-المتحقق-منها)):
نقاط نهاية مخصصة متوافقة مع OpenAI (Ollama/vLLM)، Agents، Skills، MCP (stdio/SSE/streamable-http/websocket)،
RAG API منفصل اختياري، Artifacts، OpenID Connect و SAML، locale عربي مع RTL، وسياسات احتفاظ بالمحادثات.

## Alternatives considered

| البديل | سبب عدم الاختيار |
|---|---|
| بناء تطبيق مخصص | تكلفة وزمن مرتفعان؛ إعادة بناء قدرات متوفرة |
| Open WebUI | بديل قوي؛ لم يُعتمد في ميثاق المشروع — لا يُعاد تقييمه دون سبب موثق |
| منتجات SaaS تجارية | تتعارض مع متطلبات إقامة البيانات والتحكم المؤسسي |

## Consequences

- (+) قدرات واسعة جاهزة ومجتمع نشط وإصدارات منتظمة.
- (−) فجوات متحقق منها يجب إدارتها: ترجمة عربية جزئية (~23% من المفاتيح)، لا تخصيص ألوان وقت التشغيل في v0.8.8،
  لا آلية مدعومة لتغيير الشعار، سجل تدقيق محدود، لا استيراد ملفات للوكلاء. انظر [ADR-0006](0006-upstream-first-customization.md).
- (−) ملفات Compose الرسمية للتطوير وليست آمنة للإنتاج كما هي (MongoDB `--noauth`، منافذ منشورة، دون healthchecks) — نكتب Compose خاصاً في M1.
- المشروع انتقل إلى `LibreChat-AI/LibreChat` على GitHub؛ الرابط القديم `danny-avila/LibreChat` ما زال يعمل.

## Verification

- M1: تشغيل الصورة المثبتة واجتياز `GET /health` في بيئة السحابة.
- مراجعة دورية لكل إصدار upstream جديد عبر Issue ترقية.
