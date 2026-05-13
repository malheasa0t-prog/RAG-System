# خطة دراسة HTML و CSS + شرح مشروع المساعد الذكي

هذا الملف مقسوم إلى قسمين:

1. خطة دراسة HTML و CSS من الصفر حتى بناء واجهات جيدة.
2. شرح ما عملناه في مشروع مساعد Serva-S، ولماذا رتبنا الكود بهذا الشكل.

الهدف ليس الحفظ فقط، بل أن تفهم كيف تفكر كمطور: ما وظيفة كل ملف، لماذا نقسم الكود، وكيف نختبر.

---

## القسم الأول: خطة دراسة HTML و CSS

### المدة المقترحة

إذا درست من ساعة إلى ساعتين يوميًا:

```text
4 إلى 6 أسابيع
```

إذا درست بجدية 3 ساعات يوميًا:

```text
2 إلى 3 أسابيع
```

---

## الأسبوع 1: أساسيات HTML

### الهدف

تفهم أن HTML هو هيكل الصفحة.

HTML لا يجعل الموقع جميلًا، بل يحدد:

- العناوين.
- الفقرات.
- الصور.
- الأزرار.
- الروابط.
- القوائم.
- النماذج.

### مواضيع الدراسة

- معنى HTML.
- بنية ملف HTML.
- العناصر Tags.
- الفرق بين opening tag و closing tag.
- العناصر المتداخلة.
- السمات Attributes.
- الروابط.
- الصور.
- القوائم.
- الجداول.
- النماذج Forms.

### مثال أساسي

```html
<!DOCTYPE html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>موقعي الأول</title>
  </head>
  <body>
    <h1>مرحبًا بك</h1>
    <p>هذه أول صفحة HTML أكتبها.</p>
    <a href="https://serva-s.com">زيارة المتجر</a>
  </body>
</html>
```

### شرح المثال

```html
<!DOCTYPE html>
```

يخبر المتصفح أن الملف يستخدم HTML حديث.

```html
<html lang="ar" dir="rtl">
```

يعني أن الصفحة عربية واتجاهها من اليمين إلى اليسار.

```html
<head>
```

يحتوي معلومات عن الصفحة، مثل العنوان والترميز.

```html
<body>
```

يحتوي ما يراه المستخدم على الشاشة.

### تمرين الأسبوع

ابنِ صفحة تعريف شخصية فيها:

- اسمك.
- صورة.
- فقرة عنك.
- قائمة مهارات.
- رابط إلى موقع تحبه.
- نموذج تواصل بسيط.

---

## الأسبوع 2: أساسيات CSS

### الهدف

تفهم أن CSS هو شكل الصفحة وتصميمها.

CSS يحدد:

- الألوان.
- الخطوط.
- المسافات.
- الأحجام.
- الخلفيات.
- ترتيب العناصر.

### طرق إضافة CSS

#### 1. داخل العنصر

```html
<p style="color: red;">نص أحمر</p>
```

لا ينصح بها إلا للتجربة السريعة.

#### 2. داخل ملف HTML

```html
<style>
  p {
    color: red;
  }
</style>
```

#### 3. ملف CSS منفصل

```html
<link rel="stylesheet" href="style.css" />
```

وهذه أفضل طريقة للتنظيم.

### مثال CSS

```css
body {
  font-family: Arial, sans-serif;
  background: #f5f5f5;
  color: #222;
  margin: 0;
}

h1 {
  color: #0f766e;
}

.card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 600px;
  margin: 40px auto;
}
```

### شرح المثال

```css
body
```

يستهدف الصفحة كلها.

```css
.card
```

يستهدف أي عنصر عنده class باسم `card`.

```css
margin: 40px auto;
```

يعطي مسافة فوق وتحت، ويجعل العنصر في الوسط أفقيًا.

### تمرين الأسبوع

خذ صفحة التعريف من الأسبوع الأول وأضف لها:

- خلفية.
- كرت أبيض.
- ألوان للعناوين.
- زر جميل.
- مسافات مرتبة.

---

## الأسبوع 3: Box Model و Layout

### الهدف

تفهم كيف يحسب المتصفح حجم كل عنصر.

كل عنصر في CSS يشبه صندوقًا:

```text
content
padding
border
margin
```

### مثال

```css
.box {
  width: 300px;
  padding: 20px;
  border: 1px solid #ddd;
  margin: 20px;
  box-sizing: border-box;
}
```

### أهم قاعدة

استخدم دائمًا:

```css
* {
  box-sizing: border-box;
}
```

لأنها تجعل حساب الأحجام أسهل.

### تمرين الأسبوع

ابنِ 3 كروت خدمات:

- اسم الخدمة.
- وصف.
- سعر.
- زر طلب.

---

## الأسبوع 4: Flexbox

### الهدف

ترتيب العناصر بسهولة في صف أو عمود.

### مثال

```css
.services {
  display: flex;
  gap: 16px;
}

.service-card {
  flex: 1;
}
```

### ماذا يعني هذا؟

```css
display: flex;
```

يجعل العناصر الداخلية قابلة للترتيب بجانب بعضها.

```css
gap: 16px;
```

مسافة بين العناصر.

```css
flex: 1;
```

يجعل الكروت تأخذ نفس العرض.

### تمرين الأسبوع

ابنِ قسم خدمات بثلاثة كروت بجانب بعض، وعلى الجوال اجعلها تحت بعض.

مثال responsive:

```css
@media (max-width: 700px) {
  .services {
    flex-direction: column;
  }
}
```

---

## الأسبوع 5: CSS Grid و Responsive Design

### الهدف

بناء صفحات تتغير حسب حجم الشاشة.

### مثال Grid

```css
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 800px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
```

### متى أستخدم Flexbox ومتى Grid؟

استخدم Flexbox عندما تريد ترتيب عناصر في اتجاه واحد:

```text
صف أو عمود
```

استخدم Grid عندما تريد شبكة:

```text
صفوف وأعمدة
```

### تمرين الأسبوع

ابنِ صفحة متجر مصغرة:

- Header.
- قائمة خدمات.
- Sidebar للتصنيفات.
- Footer.
- تصميم يعمل على الجوال.

---

## الأسبوع 6: مشروع تطبيقي

### المشروع

ابنِ واجهة بسيطة لمساعد متجر ذكي.

الواجهة تحتوي:

- عنوان.
- صندوق محادثة.
- حقل إدخال.
- زر إرسال.
- رسائل يمين ويسار.

### HTML

```html
<!DOCTYPE html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>مساعد المتجر</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <main class="chat-app">
      <header class="chat-header">
        <h1>مساعد المتجر الذكي</h1>
        <p>اسأل عن الخدمات والأسعار وطريقة الطلب.</p>
      </header>

      <section class="chat-box">
        <div class="message assistant">مرحبًا، كيف أساعدك اليوم؟</div>
        <div class="message user">هل خدمة CapCut متوفرة؟</div>
        <div class="message assistant">الخدمة غير متوفرة حاليًا، يمكنني اقتراح بديل متاح.</div>
      </section>

      <form class="chat-form">
        <input type="text" placeholder="اكتب رسالتك..." />
        <button type="submit">إرسال</button>
      </form>
    </main>
  </body>
</html>
```

### CSS

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: Arial, sans-serif;
  background: #f3f4f6;
  color: #111827;
}

.chat-app {
  width: min(900px, calc(100% - 32px));
  margin: 32px auto;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.chat-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.chat-header p {
  margin: 0;
  color: #6b7280;
}

.chat-box {
  min-height: 420px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  max-width: 70%;
  padding: 12px 14px;
  border-radius: 8px;
  line-height: 1.7;
}

.message.assistant {
  align-self: flex-start;
  background: #f3f4f6;
}

.message.user {
  align-self: flex-end;
  background: #0f766e;
  color: white;
}

.chat-form {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.chat-form input {
  flex: 1;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 16px;
}

.chat-form button {
  padding: 12px 20px;
  border: 0;
  border-radius: 6px;
  background: #0f766e;
  color: white;
  font-size: 16px;
  cursor: pointer;
}

@media (max-width: 600px) {
  .message {
    max-width: 90%;
  }

  .chat-form {
    flex-direction: column;
  }
}
```

---

# القسم الثاني: شرح مشروع المساعد الذكي

## ما الذي كان موجودًا؟

كان المشروع يحتوي عدة سكربتات:

- سكربت للمحادثة.
- سكربت للتقييم.
- سكربت لتعبئة الخدمات.
- سكربت لتعبئة السياسات.
- سكربت لتعبئة السيناريوهات.

لكن كان هناك تكرار:

- منطق البحث مكرر في أكثر من ملف.
- إعدادات Supabase وGoogle وGroq كانت موجودة في أكثر من مكان.
- بعض الملفات كانت كبيرة وصعبة الفهم.
- بعض السكربتات كانت تفعل أشياء خطرة مثل مسح كل embeddings.

---

## ما الذي نظفناه؟

### 1. نقل الإعدادات إلى `app_config.py`

بدل كتابة المفاتيح في كل ملف، صار لدينا ملف واحد:

```text
scripts/app_config.py
```

وظيفته:

- قراءة `.env`.
- تجهيز `SUPABASE_URL`.
- تجهيز `SUPABASE_KEY`.
- تجهيز `GOOGLE_API_KEY`.
- تجهيز `GROQ_API_KEY`.
- تجهيز `HEADERS`.
- التأكد أن المفاتيح موجودة.

الفكرة:

```text
لا تكرر الإعدادات في كل ملف.
```

---

### 2. إنشاء `rag_core.py`

هذا أهم ملف الآن.

```text
scripts/rag_core.py
```

هو عقل المشروع.

يحتوي:

- البحث في الخدمات.
- البحث في embeddings.
- معرفة حالة الخدمة.
- تحميل قواعد الأمان.
- تحميل الذاكرة.
- توليد الرد.
- حماية المخرجات.

قبل التنظيف، كان `gradio_chat.py` كبيرًا جدًا.

بعد التنظيف:

- `rag_core.py`: المنطق.
- `gradio_chat.py`: الواجهة فقط.
- `chat_ai.py`: تجربة CLI فقط.
- `eval_test.py`: التقييم فقط.

هذه قاعدة مهمة في البرمجة:

```text
افصل المنطق عن الواجهة.
```

---

## شرح أهم أجزاء `rag_core.py`

### إعداد النماذج

```python
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
main_model = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.0)
helper_model = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.0)
```

المعنى:

- `embeddings_model`: يحول النص إلى أرقام للبحث.
- `main_model`: يكتب الرد النهائي.
- `helper_model`: يساعد في إعادة صياغة السؤال وإعادة ترتيب النتائج.

---

### البحث عن الخدمات بالكلمات

```python
def lookup_services_by_keywords(question: str, limit: int = 6) -> list[dict]:
```

وظيفته:

- يبحث مباشرة في جدول `services`.
- يفيد عندما تكون حصة Google Embeddings ممتلئة.
- يقرأ حالة الخدمة مباشرة من قاعدة البيانات.

هذا مهم جدًا لمشكلة الخدمات المعطلة.

---

### تحويل الخدمة إلى نص مفهوم

```python
def service_to_context(service: dict) -> str:
```

هذه الدالة تأخذ صفًا من جدول `services` وتحوله إلى نص مثل:

```text
الخدمة: CAPCUT 6 MONTHES
الحالة: غير متوفرة حاليًا / معطلة
السعر: 3$
تنبيه مهم: هذه الخدمة معطلة وغير متوفرة للطلب حاليًا.
```

بهذا الشكل يفهم النموذج حالة الخدمة.

---

### البحث المتجهي

```python
def vector_search(question: str) -> list[dict]:
```

وظيفته:

- يحول السؤال إلى embedding.
- يبحث في `ai_documents`.
- يبحث في `ai_knowledge_documents`.

إذا فشل بسبب حد Google، يستخدم النظام البحث النصي المباشر.

---

### دمج البحثين

```python
def search_knowledge(question: str) -> list[dict]:
```

هذه الدالة تجمع:

- نتائج البحث النصي المباشر.
- نتائج البحث بالـ embeddings.

الفائدة:

```text
إذا embeddings فشل، لا يتوقف النظام تمامًا.
```

---

### توليد الإجابة

```python
def answer_question(message, history=None, session_id=None, save=True):
```

هذه أهم دالة.

تعمل كل التسلسل:

1. تستقبل سؤال العميل.
2. تعيد صياغة السؤال.
3. تبحث في قاعدة المعرفة.
4. تبني السياق.
5. تضيف قواعد الأمان.
6. ترسل كل شيء للنموذج.
7. تنظف الرد.
8. تحفظ المحادثة إذا أردنا.
9. ترجع الإجابة.

---

## لماذا صغرنا `gradio_chat.py`؟

الواجهة يجب ألا تحتوي عقل المشروع.

الواجهة وظيفتها فقط:

- تأخذ رسالة المستخدم.
- ترسلها إلى `answer_question`.
- تعرض الرد.

مثال:

```python
answer, session_id = answer_question(user_message, history, session_id, save=True)
```

هذا يجعل الملف سهل الفهم.

---

## ماذا عن `eval_test.py`؟

قبل التنظيف، كان يكرر منطق البحث والرد.

بعد التنظيف، صار يستدعي:

```python
answer_question(...)
```

وهذا أفضل لأن الاختبار الآن يقيس نفس التطبيق الحقيقي.

---

## ماذا عن الخدمات المعطلة؟

أنت طلبت ألا نحذف الخدمات المعطلة.

لذلك عملنا التالي:

- الخدمات المعطلة تدخل في المعرفة.
- لكن حالتها تكون واضحة:

```text
غير متوفرة حاليًا / معطلة
```

- المساعد لا يعرض رابط طلبها.
- المساعد لا يشجع العميل على شرائها.

هذا أفضل من حذفها، لأن العميل قد يسأل عن خدمة يعرف اسمها.

---

## كيف تحدّث الذكاء الاصطناعي؟

لا تحتاج تشغيل كل شيء كل مرة.

### إذا تغيرت الخدمات أو الأسعار أو حالة active

```bash
$env:RESET_SERVICE_DOCUMENTS='true'
python scripts/fill_ai_pro.py
Remove-Item Env:RESET_SERVICE_DOCUMENTS
```

### إذا تغيرت السياسات

```bash
$env:RESET_POLICY_DOCUMENTS='true'
python scripts/fill_policies_ai.py
Remove-Item Env:RESET_POLICY_DOCUMENTS
```

### إذا تغيرت السيناريوهات

```bash
$env:RESET_SCENARIO_DOCUMENTS='true'
python scripts/fill_scenarios_ai.py
Remove-Item Env:RESET_SCENARIO_DOCUMENTS
```

### إذا تغيرت العروض أو التصنيفات أو صفحات الموقع

```bash
python scripts/fill_public_knowledge.py
```

### إذا تغيرت قواعد الأمان

```bash
python scripts/fill_safety_rules.py
```

---

## كيف تشغل المشروع؟

### واجهة Gradio

```bash
python scripts/gradio_chat.py
```

### تجربة سطر الأوامر

```bash
python scripts/chat_ai.py
```

### اختبار الجودة

```bash
python scripts/eval_test.py
```

---

## كيف تدرس الكود الآن؟

اقرأ بالترتيب:

1. `scripts/app_config.py`
2. `scripts/rag_core.py`
3. `scripts/llm_client.py`
4. `scripts/gradio_chat.py`
5. `scripts/chat_ai.py`
6. `scripts/eval_test.py`
6. سكربتات التعبئة مثل `fill_ai_pro.py`

لا تبدأ من سكربتات التعبئة الكبيرة؛ ابدأ من القلب والواجهة.

---

## تمارين لفهم المشروع

### تمرين 1

افتح `gradio_chat.py` واكتب تعليقًا فوق كل دالة يشرح ماذا تفعل.

### تمرين 2

افتح `rag_core.py` وابحث عن:

```python
answer_question
```

ثم اكتب التسلسل الذي يحدث داخلها.

### تمرين 3

جرّب سؤال:

```text
هل CAPCUT 6 MONTHES متوفرة؟
```

وانظر كيف تظهر الحالة.

### تمرين 4

أضف test case جديد في `eval_test.py` لخدمة معطلة أخرى.

### تمرين 5

ابنِ واجهة HTML/CSS للمحادثة، ثم لاحقًا اربطها بـ API بدل Gradio.

---

## خلاصة تعليمية

أهم مفاهيم تعلمناها من المشروع:

- لا تضع المفاتيح داخل الكود.
- لا تكرر المنطق في أكثر من ملف.
- افصل الواجهة عن منطق التطبيق.
- اجعل مزود النموذج قابلًا للتبديل من `.env`، مثل `LLM_PROVIDER=openrouter`.
- اجعل قاعدة البيانات مصدر الحقيقة.
- لا تعتمد على embeddings وحدها.
- اكتب اختبارات تقيس التطبيق الحقيقي.
- اجعل الكود صغيرًا وواضحًا قدر الإمكان.

هذه مبادئ مهمة ستفيدك في أي مشروع برمجي، وليس فقط في الذكاء الاصطناعي.
