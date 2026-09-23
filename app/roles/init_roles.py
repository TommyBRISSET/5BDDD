from app.database import engine
from sqlalchemy import text


def run_init():
    with engine.connect() as conn:
        seqs = ["authors_id_seq", "books_id_seq", "app_users_id_seq", "rent_books_id_seq"]
        for seq in seqs:
            conn.execute(text(
                f"BEGIN EXECUTE IMMEDIATE 'CREATE SEQUENCE {seq} START WITH 1 INCREMENT BY 1 NOCACHE'; EXCEPTION WHEN OTHERS THEN NULL; END;"))

        conn.execute(text("BEGIN EXECUTE IMMEDIATE 'DROP ROLE app_user'; EXCEPTION WHEN OTHERS THEN NULL; END;"))
        conn.execute(text("BEGIN EXECUTE IMMEDIATE 'DROP ROLE app_admin'; EXCEPTION WHEN OTHERS THEN NULL; END;"))
        conn.execute(text("CREATE ROLE app_user"))
        conn.execute(text("CREATE ROLE app_admin"))

        conn.execute(text("GRANT SELECT ON books TO app_user"))
        conn.execute(text("GRANT SELECT ON authors TO app_user"))
        conn.execute(text("GRANT SELECT, INSERT, UPDATE ON rent_books TO app_user"))
        conn.execute(text("GRANT SELECT ON rent_books_id_seq TO app_user"))

        for table in ["books", "authors", "app_users", "rent_books"]:
            conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_admin"))
        for seq in seqs:
            conn.execute(text(f"GRANT SELECT ON {seq} TO app_admin"))

        conn.execute(text("BEGIN EXECUTE IMMEDIATE 'DROP USER alice CASCADE'; EXCEPTION WHEN OTHERS THEN NULL; END;"))
        conn.execute(text("BEGIN EXECUTE IMMEDIATE 'DROP USER bob CASCADE'; EXCEPTION WHEN OTHERS THEN NULL; END;"))

        conn.execute(text('CREATE USER alice IDENTIFIED BY "SecretAlice2026"'))
        conn.execute(text("GRANT CREATE SESSION TO alice"))
        conn.execute(text("GRANT app_admin TO alice"))

        conn.execute(text('CREATE USER bob IDENTIFIED BY "SecretBob2026"'))
        conn.execute(text("GRANT CREATE SESSION TO bob"))
        conn.execute(text("GRANT app_user TO bob"))

        conn.execute(text("DELETE FROM app_users WHERE email IN ('alice@admin.com', 'bob@user.com')"))

        insert_sql = """
            INSERT INTO app_users (id, surname, family_name, email, password, blacklist) 
            VALUES (app_users_id_seq.NEXTVAL, :surname, :family_name, :email, :password, 0)
        """

        hashed_pwd = "$argon2id$v=19$m=65536,t=3,p=4$tBZ649K/fQpGoikCPalpRw$yZBmJgF7Eoyh4mjMnAoKf+WfwA9dPlybwPWpDB+S/W0"

        conn.execute(text(insert_sql),
                     {"surname": "Alice", "family_name": "Admin", "email": "alice@admin.com", "password": hashed_pwd})
        conn.execute(text(insert_sql),
                     {"surname": "Bob", "family_name": "User", "email": "bob@user.com", "password": hashed_pwd})

        conn.commit()

if __name__ == "__main__":
    run_init()