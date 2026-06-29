import asyncio

from fastapi import HTTPException

from ..schemas import BookBrief, BookDetail, ChapterBrief, ChapterContent
from .base import SourceProvider


BOOKS = {
    "sanguo": {
        "title": "三国演义",
        "author": "罗贯中",
        "category": "古典文学",
        "status": "完结",
        "intro": "东汉末年至西晋初年间群雄割据、魏蜀吴鼎立的历史演义。",
        "cover": "/covers/sanguo.png",
        "chapters": [
            ("宴桃园豪杰三结义", "话说天下大势，分久必合，合久必分。三位豪杰因志同道合，相逢于风云际会之时。"),
            ("张翼德怒鞭督邮", "玄德治理县事，秋毫无犯，民皆感化。督邮至县，傲慢无礼，翼德闻之大怒。"),
            ("议温明董卓叱丁原", "朝廷多故，群雄各怀心志。董卓带兵入京，局势由此更添波澜。"),
        ],
    },
    "xiyou": {
        "title": "西游记",
        "author": "吴承恩",
        "category": "神魔小说",
        "status": "完结",
        "intro": "唐僧师徒西行取经，一路降妖伏魔、历经磨难的古典神魔小说。",
        "cover": "/covers/xiyou.png",
        "chapters": [
            ("灵根育孕源流出", "海外有一国土，名曰傲来国。海中有一座名山，唤为花果山。"),
            ("悟彻菩提真妙理", "美猴王漂洋过海，访师求道，终在灵台方寸山寻得门径。"),
            ("四海千山皆拱伏", "悟空归来，整顿花果山，结交四方豪杰，声名渐盛。"),
        ],
    },
    "honglou": {
        "title": "红楼梦",
        "author": "曹雪芹",
        "category": "世情小说",
        "status": "完结",
        "intro": "以贾、史、王、薛四大家族兴衰为背景，描绘大观园中的人生百态。",
        "cover": "",
        "chapters": [
            ("甄士隐梦幻识通灵", "此开卷第一回也。作者自云曾历过一番梦幻之后，将真事隐去。"),
            ("贾夫人仙逝扬州城", "冷子兴演说荣国府，将两府人物与盛衰端倪一一道来。"),
            ("托内兄如海酬训教", "黛玉辞父进京，初入荣国府，所见人物气象皆不寻常。"),
        ],
    },
}


class DemoProvider(SourceProvider):
    def __init__(self, identifier: str, name: str, delay: float = 0.03):
        self.identifier = identifier
        self.name = name
        self.base_url = "local://public-domain"
        self.delay = delay

    async def search(self, keyword: str) -> list[BookBrief]:
        await asyncio.sleep(self.delay)
        keyword = keyword.strip().lower()
        results = []
        for external_id, book in BOOKS.items():
            haystack = f"{book['title']} {book['author']} {book['category']}".lower()
            if keyword in haystack:
                results.append(
                    BookBrief(
                        external_id=external_id,
                        title=book["title"],
                        author=book["author"],
                        status=book["status"],
                        words=len(book["chapters"]) * 10000,
                        updated_at="古典公版",
                        source=self.identifier,
                        source_name=self.name,
                        cover=book["cover"],
                    )
                )
        return results

    async def get_book_detail(self, book_id: str) -> BookDetail:
        await asyncio.sleep(self.delay)
        book = BOOKS.get(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="未找到书籍")
        return BookDetail(
            external_id=book_id,
            title=book["title"],
            author=book["author"],
            status=book["status"],
            source=self.identifier,
            source_name=self.name,
            intro=book["intro"],
            category=book["category"],
            cover=book["cover"],
            chapters=[
                ChapterBrief(id=str(index), index=index, title=chapter[0])
                for index, chapter in enumerate(book["chapters"])
            ],
        )

    async def get_chapter_content(
        self, book_id: str, chapter_id: str
    ) -> ChapterContent:
        detail = await self.get_book_detail(book_id)
        try:
            index = int(chapter_id)
            title, seed = BOOKS[book_id]["chapters"][index]
        except (ValueError, IndexError):
            raise HTTPException(status_code=404, detail="未找到章节") from None
        content = "\n\n".join(
            [
                seed,
                "风过檐角，灯影在纸窗上轻轻摇曳。故事中的人各自向前，命运也在不经意间转了方向。",
                "这一段演示正文用于验证 BookHub 的排版、阅读设置和进度同步。接入真实书源后，适配器会返回完整章节内容。",
                "读到这里，不妨停一停。好的阅读器应当隐入背景，只把文字留在眼前。",
            ]
            * 4
        )
        return ChapterContent(
            id=chapter_id,
            index=index,
            title=title,
            book_external_id=detail.external_id,
            content=content,
        )
