from PIL import Image as PILImage, ImageTk
from modules.FrontEnd.CanvasMgr import Canvas_Create


class Texture:

    Name: str
    Object: ImageTk.PhotoImage

    def __init__(self, Name=str, Object=any):
        self.Name = Name
        self.Object = Object


class TextureMgr:

    TexturePool: list[Texture] = []

    @classmethod
    def AppendTexture(cls, texture: Texture):
        cls.TexturePool.append(texture)

    @classmethod
    def Request(cls, Name: str):
        for Entry in cls.TexturePool:
            if Name.lower() == Entry.Name.lower():
                return Entry.Object

        raise f"Texture Doesn't exist {Name}"

    @classmethod
    def CreateCompositeTexture(cls, name, image_paths):
        """Precomposite multiple full-canvas RGBA images into one PhotoImage.
        Reduces per-frame CoreGraphics RGBA compositing passes on macOS."""
        from modules.scaling import sf
        w, h = int(1200 * sf), int(600 * sf)
        base = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
        for path in image_paths:
            full_path = Canvas_Create.get_UI_path(path)
            img = PILImage.open(full_path).resize((w, h), PILImage.LANCZOS)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            base = PILImage.alpha_composite(base, img)
        photo = ImageTk.PhotoImage(base)
        cls.AppendTexture(Texture(name, photo))

    @classmethod
    def CreateTexture(
        cls,
        image_path=str,
        width: int | None = None,
        height: int | None = None,
        blur: int | None = None,
        mirror: bool = False,
        flip: bool = False,
        auto_contrast: bool = False,
        img_scale: int = None,
    ):
        Image = Canvas_Create.Photo_Image(
            image_path, width, height, blur, mirror, flip, auto_contrast, img_scale
        )

        cls.AppendTexture(Texture(image_path, Image))

    @classmethod
    def Initialize(cls):
        TextureMgr.CreateTexture(
            image_path="image.jpg", width=int(1200), height=int(600)
        )
        TextureMgr.CreateTexture(
            image_path="graphics.png", width=int(70 * 1.6), height=int(48 * 1.6)
        )
        TextureMgr.CreateTexture(
            image_path="graphics_active.png", width=int(70 * 1.6), height=int(48 * 1.6)
        )
        TextureMgr.CreateTexture(
            image_path="extra.png", width=int(70 * 1.6), height=int(48 * 1.6)
        )
        TextureMgr.CreateTexture(
            image_path="extra_active.png", width=int(70 * 1.6), height=int(48 * 1.6)
        )
        TextureMgr.CreateTexture(
            image_path="apply.png", width=int(70 * 1.5), height=int(48 * 1.5)
        )
        TextureMgr.CreateTexture(
            image_path="apply_active.png", width=int(70 * 1.5), height=int(48 * 1.5)
        )
        TextureMgr.CreateTexture(
            image_path="launch.png", width=int(70 * 1.5), height=int(48 * 1.5)
        )
        TextureMgr.CreateTexture(
            image_path="launch_active.png", width=int(70 * 1.5), height=int(48 * 1.5)
        )
        TextureMgr.CreateTexture(
            image_path="extract.png", width=int(70 * 1.5), height=int(48 * 1.5)
        )
        TextureMgr.CreateTexture(
            image_path="extract_active.png", width=int(70 * 1.5), height=int(48 * 1.5)
        )
        TextureMgr.CreateTexture(
            image_path="optimizer_logo.png", width=int(3316 / 10), height=int(823 / 10)
        )

        TextureMgr.CreateTexture(
            image_path="optimizer_logo_active.png",
            width=int(3316 / 10),
            height=int(823 / 10),
        )

        for i in range(1, 6):
            TextureMgr.CreateTexture(
                image_path=f"LogoAnimation/Logo_Active_{i}.png",
                width=int(3316 / 10),
                height=int(823 / 10),
            )

        # Benchmark Buttons
        TextureMgr.CreateTexture(
            image_path="benchmark_copy.png",
            width=int(115),
            height=int(43),
        )
        TextureMgr.CreateTexture(
            image_path="benchmark_copy_active.png",
            width=int(115 * 1.2),
            height=int(43 * 1.2),
        )
        TextureMgr.CreateTexture(
            image_path="benchmark_loading.png",
            width=int(115),
            height=int(43),
        )
        TextureMgr.CreateTexture(
            image_path="benchmark_loading_active.png",
            width=int(115 * 1.2),
            height=int(43 * 1.2),
        )
        TextureMgr.CreateTexture(
            image_path="benchmark_cycle.png",
            width=int(115),
            height=int(43),
        )
        TextureMgr.CreateTexture(
            image_path="benchmark_cycle_active.png",
            width=int(115 * 1.2),
            height=int(43 * 1.2),
        )
        TextureMgr.CreateTexture(
            image_path="Switch_Button.png",
            width=int(115 * 1.2),
            height=int(43 * 1.2),
        )
        TextureMgr.CreateTexture(
            image_path="Switch_Button_active.png",
            width=int(115 * 1.4),
            height=int(43 * 1.4),
        )
        TextureMgr.CreateTexture(
            image_path="Switch_Button_2.png",
            width=int(115 * 1.2),
            height=int(43 * 1.2),
        )
        TextureMgr.CreateTexture(
            image_path="Switch_Button_2_active.png",
            width=int(115 * 1.4),
            height=int(43 * 1.4),
        )
        TextureMgr.CreateTexture(
            image_path="Legacy_BG.png",
            width=1200,
            height=600,
        )
        TextureMgr.CreateTexture(
            image_path="Ryujinx_BG.png",
            width=1200,
            height=600,
        )
        TextureMgr.CreateTexture(
            image_path="Master_Sword.png",
            width=155,
            height=88,
        )
        TextureMgr.CreateTexture(
            image_path="Master_Sword2.png",
            mirror=True,
            width=155,
            height=88,
        )
        TextureMgr.CreateTexture(
            image_path="Master_Sword_active.png",
            width=int(155 * 1.0),
            height=int(88 * 1.0),
        )
        TextureMgr.CreateTexture(
            image_path="Master_Sword_active2.png",
            mirror=True,
            width=int(155 * 1.0),
            height=int(88 * 1.0),
        )
        TextureMgr.CreateTexture(
            image_path="Hylian_Shield.png",
            width=int(72 * 1.2),
            height=int(114 * 1.2),
        )
        TextureMgr.CreateTexture(
            image_path="Hylian_Shield_Active.png",
            width=int(72 * 1.2),
            height=int(114 * 1.2),
        )
        # ponytail: precomposite static overlays → 1 RGBA pass/frame instead of 2
        TextureMgr.CreateCompositeTexture(
            "ui_static_overlay",
            ["BG_Left_2.png", "BG_Right_UI.png"],
        )
        TextureMgr.CreateTexture(
            image_path="BG_Left_Cheats.png",
            width=1200,
            height=600,
        )
        TextureMgr.CreateTexture(
            image_path="BG_Left.png",
            width=1200,
            height=600,
        )
        TextureMgr.CreateTexture(
            image_path="browse.png",
            width=int(115 * 0.8),
            height=int(43 * 0.8),
        )
        TextureMgr.CreateTexture(
            image_path="browse_a.png",
            width=int(115 * 0.9),
            height=int(43 * 0.9),
        )
        TextureMgr.CreateTexture(
            image_path="autosearch.png",
            width=int(115 * 0.8),
            height=int(43 * 0.8),
        )
        TextureMgr.CreateTexture(
            image_path="autosearch_a.png",
            width=int(115 * 0.9),
            height=int(43 * 0.9),
        )
        TextureMgr.CreateTexture(
            image_path="backup.png",
            width=int(115 * 0.8),
            height=int(43 * 0.8),
        )
        TextureMgr.CreateTexture(
            image_path="backup_a.png",
            width=int(115 * 0.9),
            height=int(43 * 0.9),
        )
        TextureMgr.CreateTexture(
            image_path="shaders.png",
            width=int(115 * 0.8),
            height=int(43 * 0.8),
        )
        TextureMgr.CreateTexture(
            image_path="shaders_a.png",
            width=int(115 * 0.9),
            height=int(43 * 0.9),
        )
        TextureMgr.CreateTexture(
            image_path="main.png",
            width=int(115 * 0.7),
            height=int(43 * 0.7),
        )
        TextureMgr.CreateTexture(
            image_path="main_a.png",
            width=int(115 * 0.8),
            height=int(43 * 0.8),
        )
        TextureMgr.CreateTexture(
            image_path="cheats.png",
            width=int(115 * 0.7),
            height=int(43 * 0.7),
        )
        TextureMgr.CreateTexture(
            image_path="cheats_a.png",
            width=int(115 * 0.8),
            height=int(43 * 0.8),
        )
