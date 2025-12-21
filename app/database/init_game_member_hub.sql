-- 游戏会员之家系统 PostgreSQL 初始化脚本
-- 数据库：game_member_hub（由容器创建，脚本只负责建表/索引/种子数据）
-- 兼容：PostgreSQL 15，Docker 初始化（docker-compose.yml:47）

SET client_encoding = 'UTF8';
SET TIME ZONE 'UTC';

-- 扩展：用于生成 UUID
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================
-- 基础实体
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username        varchar(64) NOT NULL UNIQUE,
    email           varchar(255) NOT NULL UNIQUE,
    password_hash   varchar(255) NOT NULL,
    role            varchar(16) NOT NULL DEFAULT 'member',
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_users_role CHECK (role IN ('member','merchant','admin'))
);

CREATE TABLE IF NOT EXISTS merchants (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    shop_name       varchar(128) NOT NULL UNIQUE,
    contact_phone   varchar(32),
    shop_desc       text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS addresses (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_name   varchar(64) NOT NULL,
    phone           varchar(32) NOT NULL,
    province        varchar(64) NOT NULL,
    city            varchar(64) NOT NULL,
    district        varchar(64),
    detail          varchar(255) NOT NULL,
    is_default      boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_addresses_user_default ON addresses(user_id) WHERE is_default = true;

-- 分类
CREATE TABLE IF NOT EXISTS categories (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            varchar(64) NOT NULL UNIQUE,
    slug            varchar(64) NOT NULL UNIQUE,
    parent_id       uuid REFERENCES categories(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);

-- 商品
CREATE TABLE IF NOT EXISTS products (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id     uuid NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    name            varchar(128) NOT NULL,
    sku             varchar(64) UNIQUE,
    description     text,
    price           numeric(12,2) NOT NULL CHECK (price >= 0),
    stock           integer NOT NULL DEFAULT 0 CHECK (stock >= 0),
    status          varchar(8) NOT NULL DEFAULT 'on',
    popularity_score integer NOT NULL DEFAULT 0,
    views_count     integer NOT NULL DEFAULT 0,
    sales_count     integer NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_products_status CHECK (status IN ('on','off'))
);
CREATE INDEX IF NOT EXISTS idx_products_merchant ON products(merchant_id);
CREATE INDEX IF NOT EXISTS idx_products_popularity ON products(popularity_score DESC, sales_count DESC);
CREATE INDEX IF NOT EXISTS idx_products_views ON products(views_count DESC);

-- 商品-分类 多对多
CREATE TABLE IF NOT EXISTS product_categories (
    product_id      uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    category_id     uuid NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (product_id, category_id)
);
CREATE INDEX IF NOT EXISTS idx_product_categories_category ON product_categories(category_id);

-- 收藏
CREATE TABLE IF NOT EXISTS favorites (
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id      uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, product_id)
);
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);

-- =========================
-- 购物与订单
-- =========================
CREATE TABLE IF NOT EXISTS carts (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cart_items (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id         uuid NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    product_id      uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity        integer NOT NULL CHECK (quantity > 0),
    unit_price      numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_cart_items_cart_product ON cart_items(cart_id, product_id);

CREATE TABLE IF NOT EXISTS orders (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    address_id      uuid REFERENCES addresses(id) ON DELETE SET NULL,
    order_no        varchar(32) NOT NULL UNIQUE,
    status          varchar(16) NOT NULL DEFAULT 'pending',
    total_amount    numeric(12,2) NOT NULL CHECK (total_amount >= 0),
    created_at      timestamptz NOT NULL DEFAULT now(),
    paid_at         timestamptz,
    shipped_at      timestamptz,
    completed_at    timestamptz,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_orders_status CHECK (status IN ('pending','paid','shipped','completed','cancelled'))
);
CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS order_items (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        uuid NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id      uuid NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity        integer NOT NULL CHECK (quantity > 0),
    unit_price      numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (order_id, product_id)
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

CREATE TABLE IF NOT EXISTS payments (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        uuid NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    method          varchar(16) NOT NULL DEFAULT 'online',
    status          varchar(16) NOT NULL DEFAULT 'unpaid',
    amount          numeric(12,2) NOT NULL CHECK (amount >= 0),
    transaction_no  varchar(64),
    paid_at         timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_payments_method CHECK (method IN ('online','cod')),
    CONSTRAINT chk_payments_status CHECK (status IN ('unpaid','success','failed','refunded'))
);

-- =========================
-- 促销与活动
-- =========================
CREATE TABLE IF NOT EXISTS promotions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id     uuid NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    title           varchar(128) NOT NULL,
    discount_type   varchar(16) NOT NULL,
    discount_value  numeric(12,2) NOT NULL CHECK (discount_value >= 0),
    start_at        timestamptz NOT NULL,
    end_at          timestamptz NOT NULL,
    status          varchar(16) NOT NULL DEFAULT 'active',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_promotions_type CHECK (discount_type IN ('percent','fixed')),
    CONSTRAINT chk_promotions_status CHECK (status IN ('active','inactive'))
);
CREATE INDEX IF NOT EXISTS idx_promotions_merchant ON promotions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_promotions_period ON promotions(start_at, end_at);

CREATE TABLE IF NOT EXISTS promotion_products (
    promotion_id    uuid NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    product_id      uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (promotion_id, product_id)
);

-- =========================
-- 客服与交流
-- =========================
CREATE TABLE IF NOT EXISTS messages (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id            uuid REFERENCES orders(id) ON DELETE SET NULL,
    content             text NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_pair ON messages(sender_user_id, receiver_user_id, created_at DESC);

-- 社区
CREATE TABLE IF NOT EXISTS community_groups (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            varchar(128) NOT NULL UNIQUE,
    description     text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS group_members (
    group_id        uuid NOT NULL REFERENCES community_groups(id) ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at       timestamptz NOT NULL DEFAULT now(),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (group_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);

CREATE TABLE IF NOT EXISTS posts (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id        uuid NOT NULL REFERENCES community_groups(id) ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           varchar(255) NOT NULL,
    content         text NOT NULL,
    likes_count     integer NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_posts_group ON posts(group_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS comments (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id         uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content         text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id, created_at DESC);

-- =========================
-- 种子数据
-- =========================
INSERT INTO categories (id, name, slug)
VALUES
    (gen_random_uuid(), '游戏', 'games'),
    (gen_random_uuid(), '手办', 'figures')
ON CONFLICT (name) DO NOTHING;

INSERT INTO community_groups (id, name, description)
VALUES
    (gen_random_uuid(), '二次元爱好者', '围绕二次元商品与游戏的交流社区')
ON CONFLICT (name) DO NOTHING;

-- =========================
-- 视图（可选：人气商品榜单）
-- =========================
CREATE OR REPLACE VIEW v_top_popular_products AS
SELECT
    p.id,
    p.name,
    p.merchant_id,
    p.price,
    p.sales_count,
    p.views_count,
    p.popularity_score,
    p.created_at
FROM products p
ORDER BY p.popularity_score DESC, p.sales_count DESC, p.views_count DESC, p.created_at DESC;
