# المتطلبات غير الوظيفية (Non-Functional Requirements)

| الحقل | القيمة |
|---|---|
| الحالة العامة | Draft |

> **قاعدة:** لا توجد أهداف كمية معتمدة (SLA، RTO، RPO، زمن الاستجابة، عدد المستخدمين المتزامنين).
> كل قيمة كمية = **TBD** حتى تُعتمد عبر PR يشير إلى جهة الاعتماد (OD-04).

| ID | الفئة | المتطلب | الهدف الكمي | المرحلة |
|---|---|---|---|---|
| NFR-SEC-01 | Security | لا أسرار في Git؛ فحص أسرار آلي في CI | فحص ناجح لكل PR | M0 |
| NFR-SEC-02 | Security | قواعد البيانات والخدمات الداخلية غير مكشوفة (لا منافذ عامة لـ MongoDB/Search/RAG/Admin) | 0 منافذ داخلية عامة | M1 |
| NFR-SEC-03 | Security | HTTPS إلزامي لكل وصول خارجي | — | M1 |
| NFR-SEC-04 | Security | الحاويات بإصدارات مثبتة (tag + digest) ومصادر رسمية | — | M1 |
| NFR-SEC-05 | Security | تقييم مخاطر LLM (prompt injection، تسريب بيانات، صلاحيات الأدوات) قبل تفعيل الوكلاء/MCP | — | M5/M6 |
| NFR-PERF-01 | Performance | زمن أول token وزمن تحميل الواجهة | TBD | M8 |
| NFR-SCAL-01 | Scalability | عدد المستخدمين المتزامنين المدعوم | TBD | M8 |
| NFR-REL-01 | Reliability | فحوصات صحة (health checks) لكل خدمة وإعادة تشغيل تلقائية | — | M1 |
| NFR-AVL-01 | Availability | نسبة التوفر المستهدفة | TBD | M8 |
| NFR-ACC-01 | Accessibility | التوافق مع WCAG 2.1 AA للعناصر المخصصة | مستوى AA | M2 |
| NFR-MNT-01 | Maintainability | Upstream-first؛ لا fork دون ADR؛ ترقية LibreChat موثقة وقابلة للتراجع | — | M1+ |
| NFR-MNT-02 | Maintainability | المستودع مصدر الحقيقة لكل الإعدادات والتعريفات المعتمدة | — | M0+ |
| NFR-PORT-01 | Portability | نفس الصور والإعداد على Railway وWindows المحلي وUbuntu في الموقع (Docker Compose مرجعاً محمولاً) دون اعتماد إلزامي على مزايا مزوّد استضافة بعينه (ADR-0008) | — | M1 |
| NFR-PORT-02 | Portability | قابلية النقل إلى بنية تحتية سعودية معتمدة دون تغيير التطبيق | — | M8 |
| NFR-OBS-01 | Observability | سجلات مركزية ومراقبة صحة الخدمات | الأداة TBD | M6 |
| NFR-PRIV-01 | Privacy | بيانات اصطناعية فقط في بيئات غير معتمدة | 0 بيانات حقيقية | M0+ |
| NFR-PRIV-02 | Privacy | عدم إرسال بيانات مصنفة لمزوّد نموذج خارجي غير معتمد لها | — | M3+ |
| NFR-RES-01 | Data residency | تخزين ومعالجة البيانات الإنتاجية داخل المملكة وفق المتطلبات المعتمدة | المتطلب الرسمي TBD | M8 |
| NFR-DR-01 | Disaster recovery | نسخ احتياطي واستعادة مجربة لقواعد البيانات والملفات | RTO/RPO = TBD | M6 |
| NFR-AUD-01 | Auditability | سجل تدقيق لأحداث الدخول والإدارة والوصول للبيانات | نطاق السجل TBD | M6 |
| NFR-I18N-01 | Localization | العربية افتراضية مع RTL؛ الإنجليزية مدعومة | — | M2 |

## ملاحظات

- **الامتثال:** لا يُدّعى الامتثال لأي إطار تنظيمي سعودي قبل تحقق واعتماد رسمي (انظر [UR-06](BRD.md#7-متطلبات-غير-محسومة-unresolved)).
- ضوابط الأمن التفصيلية وحالتها: [docs/security/security-baseline.md](../security/security-baseline.md).
