"""Exercise all national SVG hit areas against public city locations, without saving visits."""

import os

from playwright.sync_api import sync_playwright

# One public city-centre point per ADM1; no participant location is used.
CITIES = {
    "11": (126.98, 37.57),
    "26": (129.08, 35.18),
    "27": (128.60, 35.87),
    "28": (126.71, 37.46),
    "12": (126.85, 35.16),
    "30": (127.38, 36.35),
    "31": (129.31, 35.54),
    "36": (127.29, 36.48),
    "41": (127.03, 37.27),
    "51": (127.73, 37.88),
    "43": (127.49, 36.64),
    "44": (127.15, 36.80),
    "52": (127.15, 35.82),
    "47": (128.73, 36.57),
    "48": (128.68, 35.23),
    "50": (126.53, 33.47),
}


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        page = browser.new_page()
        page.goto(os.environ["TRIPPICK_TEST_ORIGIN"] + "/api/v1/health")
        result = page.evaluate(
            """async cities => {
            const {RegionMap} = await import('/journal/renderer.js');
            const {features} = await (await fetch('/api/v1/regions')).json();
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            document.body.replaceChildren(svg);
            let selected, stop;
            const map = new RegionMap(svg, features, code => selected=code, id => stop=id);
            const places = Object.entries(cities).map(([code,[longitude,latitude]]) =>
                ({place_id:code, region_code:code, name:'FIXTURE', longitude, latitude}));
            for (const p of places) {
                map.draw('', [p]);
                const paths = [...svg.querySelectorAll('path')];
                const point = new DOMPoint(p.longitude*.8,-p.latitude);
                const hits = paths.filter(path => path.isPointInFill(point));
                if(paths.length!==Object.keys(cities).length || hits.length!==1 || !hits[0].classList.contains('recorded')) return p.region_code;
                hits[0].dispatchEvent(new MouseEvent('click'));
                if(selected !== p.region_code) return p.region_code;
                map.draw(selected, places);
                const pins = svg.querySelectorAll('circle');
                if(svg.querySelectorAll('path').length!==1 || pins.length!==1 ||
                   +pins[0].getAttribute('cx')!==point.x || +pins[0].getAttribute('cy')!==point.y) return p.region_code;
                pins[0].dispatchEvent(new MouseEvent('click'));
                if(stop !== selected) return p.region_code;
            }
            return 'ok';
        }""",
            CITIES,
        )
        assert result == "ok", result
        browser.close()
        print(
            "Current SVG district hit areas, regional filters and coordinate pins passed."
        )


if __name__ == "__main__":
    run()
