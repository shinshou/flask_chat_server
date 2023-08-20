from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    url_for,
    redirect,
    flash,
    abort,
    session,
    jsonify,
)
from flask_login import login_required, current_user
from flask_chat_server.models import (
    BlogCategory,
    BlogPost,
    Inquiry,
    UserSession,
    Message,
)

from flask_chat_server.main.forms import (
    BlogCategoryForm,
    UpdateCategoryForm,
    BlogPostForm,
    BlogSearchForm,
    InquiryForm,
)
from flask_chat_server import db

from flask_chat_server.main.image_handler import add_featured_image
from flask_chat_server import limiter

main = Blueprint("main", __name__)


@main.route("/category_maintenance", methods=["GET", "POST"])
@login_required
def category_maintenance():
    page = request.args.get("page", 1, type=int)
    blog_categories = BlogCategory.query.order_by(BlogCategory.id.asc()).paginate(
        page=page, per_page=10
    )
    form = BlogCategoryForm()
    if form.validate_on_submit():
        blog_category = BlogCategory(category=form.category.data)
        db.session.add(blog_category)
        db.session.commit()
        flash("ブログカテゴリが追加されました。")
        return redirect(url_for("main.category_maintenance"))
    elif form.errors:
        form.category.data = ""
        flash(form.errors["category"][0])
    return render_template(
        "category_maintenance.html", blog_categories=blog_categories, form=form
    )


@main.route("/<int:blog_category_id>/blog_category", methods=["GET", "POST"])
@login_required
def blog_category(blog_category_id):
    if not current_user.is_administrator():
        abort(403)
    blog_category = BlogCategory.query.get_or_404(blog_category_id)
    form = UpdateCategoryForm(blog_category_id)
    if form.validate_on_submit():
        blog_category.category = form.category.data
        db.session.commit()
        flash("ブログカテゴリが更新されました。")
        return redirect(url_for("main.category_maintenance"))
    elif request.method == "GET":
        form.category.data = blog_category.category
    return render_template("blog_category.html", form=form)


@main.route("/<int:blog_category_id>/delete_category", methods=["GET", "POST"])
@login_required
def delete_category(blog_category_id):
    if not current_user.is_administrator():
        abort(403)
    blog_category = BlogCategory.query.get_or_404(blog_category_id)
    db.session.delete(blog_category)
    db.session.commit()
    flash("ブログカテゴリが削除されました。")
    return redirect(url_for("main.category_maintenance"))


@main.route("/create_post", methods=["GET", "POST"])
def create_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        if form.picture.data:
            pic = add_featured_image(form.picture.data)
        else:
            pic = ""
        blog_post = BlogPost(
            title=form.title.data,
            text=form.text.data,
            featured_image=pic,
            user_id=current_user.id,
            category_id=form.category.data,
            summary=form.summary.data,
        )
        db.session.add(blog_post)
        db.session.commit()
        flash("ブログ投稿が作成されました。")
        return redirect("blog_maintenance")
    return render_template("create_post.html", form=form)


@main.route("/blog_maintenance")
@login_required
def blog_maintenance():
    page = request.args.get("page", 1, type=int)
    blog_posts = BlogPost.query.order_by(BlogPost.id.desc()).paginate(
        page=page, per_page=10
    )
    return render_template("blog_maintenance.html", blog_posts=blog_posts)


@main.route("/<int:blog_post_id>/blog_post")
def blog_post(blog_post_id):
    form = BlogSearchForm()

    blog_post = BlogPost.query.get_or_404(blog_post_id)
    # 最新記事の取得
    recent_blog_post = BlogPost.query.order_by(BlogPost.id.desc()).limit(5).all()

    # カテゴリの取得
    blog_categories = BlogCategory.query.order_by(BlogCategory.id.asc()).all()

    return render_template(
        "blog_post.html",
        post=blog_post,
        recent_blog_posts=recent_blog_post,
        blog_categories=blog_categories,
        form=form,
    )


@main.route("/<int:blog_post_id>/delete_post", methods=["GET", "POST"])
@login_required
def delete_post(blog_post_id):
    blog_post = BlogPost.query.get_or_404(blog_post_id)
    if blog_post.author != current_user:
        abort(403)
    db.session.delete(blog_post)
    db.session.commit()
    flash("ブログ投稿が削除されました。")
    return redirect(url_for("main.blog_maintenance"))


@main.route("/<int:blog_post_id>/update_post", methods=["GET", "POST"])
@login_required
def update_post(blog_post_id):
    blog_post = BlogPost.query.get_or_404(blog_post_id)
    if blog_post.author != current_user:
        abort(403)
    form = BlogPostForm()
    if form.validate_on_submit():
        blog_post.title = form.title.data
        if form.picture.data:
            blog_post.featured_image = add_featured_image(form.picture.data)
        blog_post.text = form.text.data
        blog_post.summary = form.summary.data
        blog_post.category_id = form.category.data
        db.session.commit()
        flash("ブログ投稿が更新されました。")
        return redirect(url_for("main.blog_post", blog_post_id=blog_post.id))
    elif request.method == "GET":
        form.title.data = blog_post.title
        form.picture.data = blog_post.featured_image
        form.text.data = blog_post.text
        form.summary.data = blog_post.summary
        form.category.data = blog_post.category_id
    return render_template("create_post.html", form=form)


@main.route("/")
def index():
    form = BlogSearchForm()
    # ブログ記事の取得
    page = request.args.get("page", 1, type=int)
    blog_posts = BlogPost.query.order_by(BlogPost.id.desc()).paginate(
        page=page, per_page=10
    )
    # 最新記事の取得
    recent_blog_post = BlogPost.query.order_by(BlogPost.id.desc()).limit(5).all()

    # カテゴリの取得
    blog_categories = BlogCategory.query.order_by(BlogCategory.id.asc()).all()

    return render_template(
        "index.html",
        blog_posts=blog_posts,
        recent_blog_posts=recent_blog_post,
        blog_categories=blog_categories,
        form=form,
    )


@main.route("/search", methods=["GET", "POST"])
def search():
    form = BlogSearchForm()
    searchtext = ""

    if form.validate_on_submit():
        searchtext = form.searchtext.data

    if request.method == "GET":
        form.searchtext.data = ""

    # ブログ記事の取得
    page = request.args.get("page", 1, type=int)
    blog_posts = (
        BlogPost.query.filter(
            (BlogPost.text.contains(searchtext))
            | (BlogPost.title.contains(searchtext))
            | (BlogPost.summary.contains(searchtext))
        )
        .order_by(BlogPost.id.desc())
        .paginate(page=page, per_page=10)
    )
    # 最新記事の取得
    recent_blog_post = BlogPost.query.order_by(BlogPost.id.desc()).limit(5).all()

    # カテゴリの取得
    blog_categories = BlogCategory.query.order_by(BlogCategory.id.asc()).all()

    return render_template(
        "index.html",
        blog_posts=blog_posts,
        recent_blog_posts=recent_blog_post,
        blog_categories=blog_categories,
        form=form,
        searchtext=searchtext,
    )


@main.route("/<int:blog_category_id>/category_posts")
def category_posts(blog_category_id):
    form = BlogSearchForm()

    # カテゴリ名を取得
    blog_category = BlogCategory.query.filter_by(id=blog_category_id).first_or_404()
    # ブログ記事の取得
    page = request.args.get("page", 1, type=int)
    blog_posts = (
        BlogPost.query.filter_by(category_id=blog_category_id)
        .order_by(BlogPost.id.desc())
        .paginate(page=page, per_page=10)
    )
    # 最新記事の取得
    recent_blog_post = BlogPost.query.order_by(BlogPost.id.desc()).limit(5).all()

    # カテゴリの取得
    blog_categories = BlogCategory.query.order_by(BlogCategory.id.asc()).all()

    return render_template(
        "index.html",
        blog_posts=blog_posts,
        recent_blog_posts=recent_blog_post,
        blog_categories=blog_categories,
        blog_category=blog_category,
        form=form,
    )


@main.route("/inquiry", methods=["GET", "POST"])
def inquiry():
    form = InquiryForm()
    if form.validate_on_submit():
        inquiry = Inquiry(
            name=form.name.data,
            email=form.email.data,
            title=form.title.data,
            text=form.text.data,
        )
        db.session.add(inquiry)
        db.session.commit()
        flash("お問い合わせが送信されました。")
        return redirect(url_for("main.inquiry"))
    return render_template("inquiry.html", form=form)


@main.route("/inquiry_maintenance")
def inquiry_maintenance():
    page = request.args.get("page", 1, type=int)
    inquiries = Inquiry.query.order_by(Inquiry.id.desc()).paginate(
        page=page, per_page=10
    )
    return render_template("inquiry_maintenance.html", inquiries=inquiries)


@main.route("/<int:inquiry_id>/display_inquiry")
@login_required
def display_inquiry(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    form = InquiryForm()
    form.name.data = inquiry.name
    form.email.data = inquiry.email
    form.title.data = inquiry.title
    form.text.data = inquiry.text
    return render_template("inquiry.html", form=form, inquiry_id=inquiry_id)


@main.route("/<int:inquiry_id>/delete_inquiry", methods=["GET", "POST"])
@login_required
def delete_inquiry(inquiry_id):
    inquiries = Inquiry.query.get_or_404(inquiry_id)
    if not current_user.is_administrator():
        abort(403)
    db.session.delete(inquiries)
    db.session.commit()
    flash("お問い合わせが削除されました。")
    return redirect(url_for("main.inquiry_maintenance"))


@main.route("/info")
def info():
    return render_template("info.html")


@main.route("/chat_session", methods=["GET"])
# @limiter.limit("6 per minute")
def chat_session():
    import uuid

    try:
        print("chat_session")
        # ページがリロードされるごとにセッションをリセットする。つまりセッションではない。セッションを利用したい場合はreset_session()をコメントアウトすること
        # ログインがないため基本的には毎回セッションが作成される。
        # reset_session()
        if "session_id" not in session:
            session_id = str(uuid.uuid4())
            session["session_id"] = session_id
        else:
            session_id = session["session_id"]
        chat_session = UserSession.query.get(session_id)
        if chat_session is None:
            chat_session = UserSession(session_id=session_id)
            db.session.add(chat_session)
            db.session.commit()

        print(f"session_id is {session_id}")
        return jsonify({"session_id": session_id})

    except Exception as e:
        return jsonify({f"error": "chat_sessionエラーが発生しました。内容{e}"})


def reset_session():
    session.pop("session_id", None)  # Remove session_id from the session
    print("セッションリセットされました！！")


@main.route("/save_chat", methods=["POST"])
# @limiter.limit("6 per minute")
def save_chat():
    data = request.json
    message = data.get("message")
    client_session_id = data.get("session_id")
    chat_history_id = data.get("chat_history_id")
    print("save_chat")
    session_obj = UserSession.query.get(client_session_id)

    if session_obj:
        print(
            {
                f"Session ID:{session_obj.session_id},user_id:{session_obj.user_id},created_at:{session_obj.created_at},title:{session_obj.title}"
            }
        )
    else:
        print("エラー：ストリームの際のチャット履歴の保存プログラム。セッションオブジェクトを見つけられませんでした。")
        return jsonify({"error": f"セッションオブジェクトが見つかりません。session_obj:{session_obj}"}), 404

    # 会話履歴の保存
    new_message = Message(
        chat_history_id=chat_history_id, session_id=client_session_id, content=message
    )
    db.session.add(new_message)
    db.session.commit()
    return jsonify({"success": "Chat history saved successfully"}), 200


@main.route("/chat_sse", methods=["GET"])
# @limiter.limit("6 per minute")
def chat_sse():
    MAX_HISTORY_CHARS = 2000  # 会話を記憶する最大量
    client_session_id = request.args.get("data")

    session_obj = UserSession.query.get(client_session_id)
    messages = (
        Message.query.filter_by(session_id=session_obj.session_id)
        .order_by(Message.create_at)
        .all()
    )
    if not messages:
        print("chat_sseエラー：メッセージが保存されていません。")
        return

    # ユーザーからの質問内容を判断する。
    last_chat_message = messages[-1]
    judge_question = judge_user_question(last_chat_message)

    data = {
        "history": [
            {"role": m.role, "action": m.action, "content": m.content} for m in messages
        ]
    }
    chat_history = get_chat_history(
        data, max_history_chars=MAX_HISTORY_CHARS
    )  # max_iistory_charsは会話履歴の切り詰め

    """
        ここで会話履歴をGPTに判断させて条件分岐を行う
    """

    if "generate" in judge_question.get("kind"):
        return Response(
            generate_text("私は福祉の仕事についてお話をするAIチャットボットです。このメッセージにはお答えすることができません。"),
            content_type="text/event-stream",
        )
    elif "related" in judge_question.get("kind"):
        message = chat_history
        return Response(
            ask_gpt(message),
            content_type="text/event-stream",
        )
    else:
        return Response(
            generate_text("私は福祉の仕事についてお話をするAIチャットボットです。このメッセージにはお答えすることができません。"),
            content_type="text/event-stream",
        )


def generate_text(text):
    import time

    for s in text.replace("\n", "<br>"):
        time.sleep(0.05)
        yield f"data:{s}\n\n"


def get_chat_history(data, max_history_chars=500):
    import copy

    data_copy = copy.deepcopy(data)
    # IDの削除。現状これは使っていない
    [dic.pop("id") for dic in data_copy["history"] if "id" in dic.keys()]

    new_history = []
    current_chars = 0
    for dic in reversed(data_copy["history"]):
        # 文字数の計算
        content_length = (
            len(dic["role"]) + len(dic["content"]) + 2
        )  # ': ' and '\n' are included
        current_chars += content_length

        # 現在の文字数と最大文字数を比較
        if current_chars <= max_history_chars:
            new_history.append(dic)
        elif current_chars - content_length < max_history_chars:
            remaining_chars = max_history_chars - current_chars + content_length
            dic["content"] = dic["content"][:remaining_chars]
            new_history.append(dic)
        else:
            break
    new_history.reverse()  # 時系列順に並び替える
    return new_history


"""
    サイト訪問者の質問に対して回答をする。
    そのときに質問内容によって、AIの回答方法をファンクションコーリングにより条件分岐する。
    1,normalQuestion:通常の質問。特に独自データなどを必要としない質問。WEBの最新情報を反映した結果を回答するようにする。
    2,uniqueQuestion:独自データに対する質問。pineconeに回答を探しに行く。
    3,notAnswerQuestion:不適切な質問、回答に値しない質問。
    
    1〜3をファンクションコーリングで条件分岐を行い。それに伴ってsystempromptを決定する。
    systempromptも2〜3種類が必要。
"""


def ask_gpt(message):
    from langchain.chains import RetrievalQA
    from langchain.chat_models import ChatOpenAI
    import openai
    import os
    from openai.error import RateLimitError, ServiceUnavailableError

    openai.api_key = os.environ.get("OPENAI_API_KEY")

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)

    system_prompt = """
        あなたは福祉関係の仕事に努めている男性です。
        福祉の仕事についての相談や仕事を行う上での必要な知識を質問者に回答します。
        福祉に関係のない質問については、答えないでください。
        答えてしまうとあなたのせいで、関係のない無実の人たちが被害を受けます。
        福祉以外の質問については、「専門外の質問です。福祉についてなにか質問はありますか？」と回答してください。
    """

    user_prompt = f"""
    ■お客様のご要望(会話履歴):\n{message}\n\n ,
    """

    try:
        response = openai.ChatCompletion.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="gpt-3.5-turbo",
            temperature=0.5,
            stream=True,
            max_tokens=500,
        )
    except RateLimitError as e:
        error_message = "現在サーバーが過不可です。しばらく時間をおいてからお試しください。"
        output_content = error_message
        # logging.debug(f"RateLimitError: \ne:{e} \nerror_message:{error_message}")
        print(f"RateLimitError: \ne:{e} \nerror_message:{error_message}")
        # save_to_db_message(output_content, session_id, chat_history_id, action="エラーメッセージ")
        yield f"data: {error_message}\n{e}\n\n"
    except ServiceUnavailableError as e:
        error_message = "現在サーバーが過不可です。しばらく時間をおいてからお試しください。"
        output_content = error_message
        # logging.debug(f"ServiceUnavailableError: \ne:{e} \nerror_message:{error_message}")
        print(f"ServiceUnavailableError: \ne:{e} \nerror_message:{error_message}")
        # save_to_db_message(output_content, session_id, chat_history_id, action="エラーメッセージ")
        yield f"data: {error_message}\n{e}\n\n"

    for res in response:
        try:
            if res["choices"][0]["finish_reason"] != "stop":
                content = res["choices"][0]["delta"]["content"]
                # content = content.replace("\n", "<br>")
                yield f"data: {content}\n\n"
            else:
                yield f"data: stop\n\n"
                break
            pass
        except KeyError:
            print(res["choices"][0]["finish_reason"])
            if (
                res["choices"][0]["finish_reason"] is not None
                and res["choices"][0]["finish_reason"] != "stop"
            ):
                yield f"data: stop_質問文が長すぎるため、短くしてお試しください。\n\n"
                break
            elif res["choices"][0]["finish_reason"] == "stop":
                yield f"data: stop\n\n"
                break
            pass


def judge_user_question(message):
    import json
    import openai
    import os
    from openai.error import RateLimitError, ServiceUnavailableError

    openai.api_key = os.environ.get("OPENAI_API_KEY")

    system_prompt = """
        あなたは福祉についてのHPを運営しています。
        福祉の仕事についての相談や仕事を行う上での必要な知識を質問者の質問から読み取り、回答します。
    """

    functions = [
        {
            "name": "user_question_to_answer",
            "description": "ユーザーからの質問内容を受け、回答します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "ユーザーからの質問の内容要約。",
                    },
                    "kind": {
                        "type": "string",
                        "description": "質問の種別。例1）general = 運営しているHPと関係のない質問。例2）related = 運営しているHPと関係のある質問。例3）other = 暴言などの不適切な質問。",
                    },
                },
                "required": ["question", "kind"],
            },
        }
    ]

    messages = [
        {"role": "system", "content": f"{system_prompt}"},
        {"role": "user", "content": f"{message.content}"},
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=functions,
            function_call={"name": "user_question_to_answer"},
        )
    except RateLimitError as e:
        error_message = "現在サーバーが過不可です。しばらく時間をおいてからお試しください。"
        print(f"RateLimitError: \ne:{e} \nerror_message:{error_message}")
        return f"Error at judge_user_question: {error_message}\n{e}\n\n"
    except ServiceUnavailableError as e:
        error_message = "現在サーバーが過不可です。しばらく時間をおいてからお試しください。"
        print(f"ServiceUnavailableError: \ne:{e} \nerror_message:{error_message}")
        return f"Error at judge_user_question: {error_message}\n{e}\n\n"
    response_message = response["choices"][0]["message"]
    # 設定したファンクションコーリングがAI側で使うと判断された場合。
    if response_message.get("function_call"):
        function_args = json.loads(response_message["function_call"]["arguments"])
        print(function_args)
        return function_args
    else:
        error_msg = "エラー：judge_user_questionの強制ファンクションコールが発火しませんでした。"
        print(error_msg)
        return None
