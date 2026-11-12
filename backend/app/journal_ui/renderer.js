// SVG coordinates are projected from GeoJSON [longitude, latitude], north up.
const NS = "http://www.w3.org/2000/svg";
function project(lon, lat) {
  return [lon * 0.8, -lat];
}
function svgNode(tag, attrs) {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}
export class RegionMap {
  constructor(svg, features, onRegion, onPlace) {
    this.svg = svg;
    this.onRegion = onRegion;
    this.onPlace = onPlace;
    this.shapes = features.map((f) => {
      const polys =
        f.geometry.type === "Polygon"
          ? [f.geometry.coordinates]
          : f.geometry.coordinates;
      const rings = polys.flat().map((r) => r.map(([x, y]) => project(x, y)));
      return {
        p: f.properties,
        path: rings
          .map((r) => "M" + r.map((p) => p.join(",")).join("L") + "Z")
          .join(""),
        points: rings.flat(),
      };
    });
    svg.onpointerdown = (e) => {
      this.drag = [e.clientX, e.clientY];
      this.moved = false;
    };
    svg.onpointermove = (e) => {
      if (!this.drag || !e.buttons || !this.region) return;
      const dx = e.clientX - this.drag[0],
        dy = e.clientY - this.drag[1];
      if (Math.abs(dx) + Math.abs(dy) < 3) return;
      const scale = svg.getScreenCTM()?.a;
      if (!scale) return;
      this.box[0] -= dx / scale;
      this.box[1] -= dy / scale;
      this.drag = [e.clientX, e.clientY];
      this.moved = true;
      this.view();
    };
    svg.onpointerup = () => (this.drag = null);
  }
  view() {
    this.svg.setAttribute("viewBox", this.box.join(" "));
  }
  zoom(factor) {
    if (!this.region) return;
    const [x, y, w, h] = this.box;
    if (
      w * factor < this.initialWidth / 16 ||
      w * factor > this.initialWidth * 2
    )
      return;
    this.box = [
      x + (w * (1 - factor)) / 2,
      y + (h * (1 - factor)) / 2,
      w * factor,
      h * factor,
    ];
    this.view();
  }
  draw(region, places) {
    this.region = region;
    this.svg.replaceChildren();
    const visible = this.shapes.filter((s) => !region || s.p.code === region);
    const points = visible.flatMap((s) => s.points);
    const xs = points.map((p) => p[0]),
      ys = points.map((p) => p[1]);
    let x = Math.min(...xs),
      y = Math.min(...ys),
      w = Math.max(...xs) - x,
      h = Math.max(...ys) - y;
    this.box = [x - w * 0.07, y - h * 0.07, w * 1.14, h * 1.14];
    this.initialWidth = this.box[2];
    this.view();
    for (const s of visible) {
      const path = svgNode("path", {
        d: s.path,
        "fill-rule": "evenodd",
        class: places.some((v) => v.region_code === s.p.code) ? "recorded" : "",
      });
      path.onclick = () => {
        if (!region && !this.moved) this.onRegion(s.p.code);
      };
      this.svg.append(path);
    }
    if (region)
      for (const v of places.filter(
        (v) => v.region_code === region && v.latitude != null,
      )) {
        const [cx, cy] = project(v.longitude, v.latitude);
        const pin = svgNode("circle", {
          cx,
          cy,
          r: Math.max(w, h) / 65,
          "aria-label": v.name,
        });
        pin.onclick = () => {
          if (!this.moved) this.onPlace(v.place_id);
        };
        this.svg.append(pin);
      }
  }
}
