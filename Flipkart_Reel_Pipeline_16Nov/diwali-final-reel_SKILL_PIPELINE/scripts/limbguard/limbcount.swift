// limbcount (22-Nov): counts hands, faces and bodies in pictures with Apple's Vision framework (free, local, no network).
// usage: limbcount a.jpg b.png ...   -> JSON array [{file, hands, hand_conf, faces, bodies, error}]
import Foundation
import Vision
import ImageIO

struct Out: Codable { var file: String; var hands: Int; var hand_conf: [Float]; var faces: Int; var bodies: Int; var error: String?; var hand_boxes: [[Float]]?; var sal: [Float]?; var objs: [[Float]]?; var face_boxes: [[Float]]? }

func load(_ path: String) -> CGImage? {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil) else { return nil }
    return CGImageSourceCreateImageAtIndex(src, 0, nil)
}

var results: [Out] = []
for path in CommandLine.arguments.dropFirst() {
    guard let img = load(path) else { results.append(Out(file: path, hands: 0, hand_conf: [], faces: 0, bodies: 0, error: "cannot read")); continue }
    let handReq = VNDetectHumanHandPoseRequest(); handReq.maximumHandCount = 6
    let faceReq = VNDetectFaceRectanglesRequest()
    let bodyReq = VNDetectHumanBodyPoseRequest()
    let salReq = VNGenerateAttentionBasedSaliencyImageRequest()
    let objReq = VNGenerateObjectnessBasedSaliencyImageRequest()
    do { try VNImageRequestHandler(cgImage: img, options: [:]).perform([handReq, faceReq, bodyReq, salReq, objReq]) }
    catch { results.append(Out(file: path, hands: 0, hand_conf: [], faces: 0, bodies: 0, error: "\(error)")); continue }
    var confs: [Float] = []
    var boxes: [[Float]] = []
    for o in handReq.results ?? [] {
        let pts = ((try? o.recognizedPoints(.all))?.values.filter { $0.confidence > 0.3 }) ?? []
        if o.confidence > 0.5 && pts.count >= 12 {
            confs.append(o.confidence)
            let xs = pts.map { Float($0.location.x) }, ys = pts.map { Float($0.location.y) }
            boxes.append([xs.min()!, ys.min()!, xs.max()! - xs.min()!, ys.max()! - ys.min()!])
        }
    }
    var sal: [Float]? = nil
    if let r = salReq.results?.first, let objs = r.salientObjects, !objs.isEmpty {
        let u = objs.map { $0.boundingBox }.reduce(objs[0].boundingBox) { $0.union($1) }
        sal = [Float(u.minX), Float(u.minY), Float(u.width), Float(u.height)]
    }
    let faceObs = (faceReq.results ?? []).filter { $0.confidence > 0.6 }
    let faces = faceObs.count
    let fboxes: [[Float]] = faceObs.map { [Float($0.boundingBox.minX), Float($0.boundingBox.minY), Float($0.boundingBox.width), Float($0.boundingBox.height)] }
    let oboxes: [[Float]] = (objReq.results?.first?.salientObjects ?? []).map { [Float($0.boundingBox.minX), Float($0.boundingBox.minY), Float($0.boundingBox.width), Float($0.boundingBox.height)] }
    let bodies = (bodyReq.results ?? []).filter { $0.confidence > 0.3 }.count
    results.append(Out(file: path, hands: confs.count, hand_conf: confs, faces: faces, bodies: bodies, error: nil, hand_boxes: boxes, sal: sal, objs: oboxes, face_boxes: fboxes))
}
let data = try! JSONEncoder().encode(results)
print(String(data: data, encoding: .utf8)!)
