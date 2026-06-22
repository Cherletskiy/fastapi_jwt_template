"""seed RBAC base data

Revision ID: f14931e9e535
Revises: 53d82502ab1f
Create Date: 2025-10-29 20:11:57.917393

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, String, Text, Integer, Boolean
from datetime import datetime
import bcrypt


# revision identifiers, used by Alembic.
revision: str = 'f14931e9e535'
down_revision: Union[str, None] = '53d82502ab1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем объекты таблиц для bulk_insert
    roles_table = table('roles',
                        column('name', String),
                        column('description', Text)
                        )

    permissions_table = table('permissions',
                              column('name', String),
                              column('description', Text)
                              )

    users_table = table('users',
                        column('username', String),
                        column('email', String),
                        column('hashed_password', String),
                        column('first_name', String),
                        column('last_name', String),
                        column('middle_name', String),
                        column('is_active', Boolean),
                        column('created_at', sa.TIMESTAMP)
                        )

    user_roles_table = table('user_roles',
                             column('user_id', Integer),
                             column('role_id', Integer)
                             )

    role_permissions_table = table('role_permissions',
                                   column('role_id', Integer),
                                   column('permission_id', Integer)
                                   )

    # 1. Базовые роли
    print("Создаем роли...")
    op.bulk_insert(roles_table, [
        {'name': 'user', 'description': 'Обычный пользователь'},
        {'name': 'moderator', 'description': 'Модератор'},
        {'name': 'admin', 'description': 'Администратор'}
    ])

    # 2. Базовые разрешения
    print("Создаем разрешения...")
    op.bulk_insert(permissions_table, [
        {'name': 'profile:read', 'description': 'Чтение профиля'},
        {'name': 'profile:write', 'description': 'Редактирование профиля'},
        {'name': 'users:read', 'description': 'Просмотр пользователей'},
        {'name': 'users:write', 'description': 'Редактирование пользователей'},
        {'name': 'admin:access', 'description': 'Доступ к админ-панели'}
    ])

    # 3. Тестовые пользователи
    print("Создаем тестовых пользователей...")

    # Хешируем пароли (все 'password123')
    hashed_password = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode('utf-8')

    op.bulk_insert(users_table, [
        {
            'username': 'regular_user',
            'email': 'user@example.com',
            'hashed_password': hashed_password,
            'first_name': 'Иван',
            'last_name': 'Петров',
            'middle_name': 'Сергеевич',
            'is_active': True,
            'created_at': datetime.utcnow()
        },
        {
            'username': 'admin_user',
            'email': 'admin@example.com',
            'hashed_password': hashed_password,
            'first_name': 'Админ',
            'last_name': 'Админов',
            'middle_name': 'Админович',
            'is_active': True,
            'created_at': datetime.utcnow()
        }
    ])

    # 4. Связи ролей и разрешений
    print("Настраиваем связи ролей-разрешений...")

    # User permissions
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p 
        WHERE r.name = 'user' AND p.name IN ('profile:read', 'profile:write')
    """)

    # Moderator permissions
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p 
        WHERE r.name = 'moderator' AND p.name IN ('profile:read', 'profile:write', 'users:read')
    """)

    # Admin permissions (все)
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p 
        WHERE r.name = 'admin'
    """)

    # 5. Назначаем роли пользователям
    print("Назначаем роли пользователям...")

    # regular_user → user
    op.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id FROM users u, roles r 
        WHERE u.email = 'user@example.com' AND r.name = 'user'
    """)

    # admin_user → admin
    op.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id FROM users u, roles r 
        WHERE u.email = 'admin@example.com' AND r.name = 'admin'
    """)

    print("✅ Тестовые данные созданы!")


def downgrade() -> None:
    # Очищаем данные в правильном порядке (из-за foreign keys)
    op.execute("DELETE FROM role_permissions")
    op.execute("DELETE FROM user_roles")
    op.execute("DELETE FROM users WHERE email IN ('user@example.com', 'admin@example.com')")
    op.execute("DELETE FROM permissions")
    op.execute("DELETE FROM roles")