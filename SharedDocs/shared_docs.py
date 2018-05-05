from uuid import uuid4

from flask import (
    Flask, render_template, url_for, redirect,
    request, Response, jsonify)

from utils import (
    create_new_doc, doc_exists, read_doc, copy_doc,
    merge_docs, DocumentLock, get_sync_uid, build_doc_path)


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/docs/')
def new_doc():
    uid = uuid4().hex
    create_new_doc(uid)
    return redirect(url_for('edit_doc', doc_uid=uid))


@app.route('/docs/<doc_uid>')
def edit_doc(doc_uid):
    if not doc_exists(doc_uid):
        return jsonify(status_code=-1,
                       msg="Document Does Not Exist!")
    sync_uid = get_sync_uid(request)
    copy_doc(build_doc_path(doc_uid),
             build_doc_path(doc_uid, sync_uid + '.md'))
    doc_text = read_doc(doc_uid, sync_uid + '.md')
    resp = Response(render_template(
        'doc.html', doc_uid=doc_uid, doc_text=doc_text))
    resp.set_cookie('SYNC_UID', sync_uid)
    return resp

@app.route('/docs/sync/<doc_uid>', methods=['POST'])
def sync_doc(doc_uid):
    if not doc_exists(doc_uid):
        return jsonify(status_code=-1,
                       data="Document Does Not Exist!")
    elif not 'SYNC_UID' in request.cookies:
        return jsonify(status_code=-2,
                       data="Invalid SYNC_UID!")
    sync_uid = request.cookies['SYNC_UID']
    doc = request.form['doc']
    # Lock doc preventing race condition
    with DocumentLock(doc_uid):
        # Merge into server document
        merge_docs(doc_uid, sync_uid, doc)
        return jsonify(status_code=0,
                       data=read_doc(doc_uid, sync_uid + '.md'))

if __name__ == '__main__':
    app.run('0.0.0.0')
