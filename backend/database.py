from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class CodeHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(20), nullable=False)
    code = db.Column(db.Text, nullable=False)
    input = db.Column(db.Text, default="")
    output = db.Column(db.Text, default="")
    success = db.Column(db.Boolean, default=True)
    is_saved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "language": self.language,
            "code": self.code,
            "input": self.input,
            "output": self.output,
            "success": self.success,
            "is_saved": self.is_saved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def log_execution(language, code, input_text, output, success):
    entry = CodeHistory(
        language=language,
        code=code,
        input=input_text,
        output=output,
        success=success,
    )
    db.session.add(entry)
    db.session.commit()
    _cleanup_old_entries()
    return entry


def get_recent(limit=3):
    return CodeHistory.query.order_by(CodeHistory.created_at.desc()).limit(limit).all()


def get_saved():
    return (
        CodeHistory.query.filter_by(is_saved=True)
        .order_by(CodeHistory.created_at.desc())
        .all()
    )


def toggle_save(entry_id):
    entry = db.session.get(CodeHistory, entry_id)
    if not entry:
        return None
    entry.is_saved = not entry.is_saved
    db.session.commit()
    return entry


def delete_entry(entry_id):
    entry = db.session.get(CodeHistory, entry_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def _cleanup_old_entries():
    keep_ids = [
        row.id
        for row in CodeHistory.query.filter_by(is_saved=False)
        .order_by(CodeHistory.created_at.desc())
        .limit(20)
        .all()
    ]
    if len(keep_ids) < 20:
        return
    CodeHistory.query.filter(
        CodeHistory.is_saved == False,
        ~CodeHistory.id.in_(keep_ids),
    ).delete(synchronize_session="fetch")
    db.session.commit()
