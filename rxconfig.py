import reflex as rx

config = rx.Config(
    app_name="mychat_reflex",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
