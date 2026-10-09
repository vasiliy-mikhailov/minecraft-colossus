"""Write ColossusModel.java, ColossusEyesLayer.java and colossus.bbmodel from build.py's geometry."""
import base64, json, math, os, uuid
import numpy as np
import build as B

OUT = B.OUT

def F(v):
    v = float(v)
    if abs(v - round(v)) < 1e-6:
        return f'{int(round(v))}.0F'
    return f'{v:g}F'

def children(bone):
    return [n for n, b in B.BONES.items() if b['parent'] == bone]

# ---- sanity: UV rects must not overlap and must stay inside the texture
occ = np.zeros((B.TH, B.TW), int)
for p in B.PARTS:
    _, _, w, h, d = B.footprint(p)
    u, v = p['u'], p['v']
    for (x0, y0, ww, hh) in ((u + d, v, 2 * w, d), (u, v + d, 2 * (w + d), h)):
        assert x0 + ww <= B.TW and y0 + hh <= B.TH, p['name']
        occ[y0:y0 + hh, x0:x0 + ww] += 1
assert occ.max() == 1, 'UV overlap'

# ---------------------------------------------------------------- Java
FIELD = {'body': 'body', 'head': 'head', 'right_arm': 'rightArm', 'left_arm': 'leftArm', 'sword': 'sword',
         'right_leg': 'rightLeg', 'left_leg': 'leftLeg'}

def bone_java(bone, parent_var, lines, indent='        '):
    b = B.BONES[bone]
    piv = B.mc_abs_pivot(bone)
    if b['parent'] is None:
        off = np.array([0.0, 24.0, 0.0])
    else:
        off = piv - B.mc_abs_pivot(b['parent'])
    cubes = [p for p in B.PARTS if p['bone'] == bone]
    var = 'p_' + bone
    lines.append(f'{indent}PartDefinition {var} = {parent_var}.addOrReplaceChild("{bone}", CubeListBuilder.create()')
    for p in cubes:
        _, _, w, h, d = B.footprint(p)
        x = p['x0'] - piv[0]; y = (24 - p['H1']) - piv[1]; z = p['z0'] - piv[2]
        lines.append(f'{indent}        .texOffs({p["u"]}, {p["v"]}).addBox({F(x)}, {F(y)}, {F(z)}, {F(w)}, {F(h)}, {F(d)}) // {p["name"]}')
    rx, ry, rz = b['rot']
    if any(abs(r) > 1e-9 for r in (rx, ry, rz)):
        pose = f'PartPose.offsetAndRotation({F(off[0])}, {F(off[1])}, {F(off[2])}, {F(rx)}, {F(ry)}, {F(rz)})'
    else:
        pose = f'PartPose.offset({F(off[0])}, {F(off[1])}, {F(off[2])})'
    lines.append(f'{indent}        , {pose});')
    for c in children(bone):
        bone_java(c, var, lines, indent)

mesh = []
bone_java('root', 'partdefinition', mesh)
mesh = '\n'.join(mesh)

java = f'''package net.colossus.client.model;

import net.minecraft.client.model.HierarchicalModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;

/**
 * Colossus - blocky armoured knight, ~1.6x player height (52 px tall, {B.TW}x{B.TH} texture).
 * NeoForge / Minecraft 1.21.1, Mojang mappings. Ground is at model y = 24 (standard living-entity origin),
 * so the renderer needs no extra scale/translate. Bones: root -> body, head, right_arm (-> sword), left_arm,
 * right_leg, left_leg. Generated from colossus.bbmodel geometry (Blockbench "Modded Entity", flip-Y).
 */
public class ColossusModel<T extends Entity> extends HierarchicalModel<T> {{
    public static final ModelLayerLocation LAYER_LOCATION =
            new ModelLayerLocation(ResourceLocation.fromNamespaceAndPath("colossus", "colossus"), "main");
    public static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath("colossus", "textures/entity/colossus.png");
    public static final ResourceLocation EYES_TEXTURE =
            ResourceLocation.fromNamespaceAndPath("colossus", "textures/entity/colossus_eyes.png");

    /** Walk tuning: stride amplitude from the brief, reduced arm swing (sword arm less), heavy body bob. */
    private static final float STRIDE = 1.4F;
    private static final float ARM_SWING = 0.8F;
    private static final float SWORD_ARM_FACTOR = 0.45F;
    private static final float FREE_ARM_FACTOR = 0.75F;
    private static final float BOB = 1.5F;

    private final ModelPart root;
    private final ModelPart body;
    private final ModelPart head;
    private final ModelPart rightArm;
    private final ModelPart leftArm;
    private final ModelPart sword;
    private final ModelPart rightLeg;
    private final ModelPart leftLeg;

    public ColossusModel(ModelPart root) {{
        this.root = root;
        ModelPart colossus = root.getChild("root");
        this.body = colossus.getChild("body");
        this.head = colossus.getChild("head");
        this.rightArm = colossus.getChild("right_arm");
        this.leftArm = colossus.getChild("left_arm");
        this.sword = this.rightArm.getChild("sword");
        this.rightLeg = colossus.getChild("right_leg");
        this.leftLeg = colossus.getChild("left_leg");
    }}

    public static LayerDefinition createBodyLayer() {{
        MeshDefinition meshdefinition = new MeshDefinition();
        PartDefinition partdefinition = meshdefinition.getRoot();

{mesh}

        return LayerDefinition.create(meshdefinition, {B.TW}, {B.TH});
    }}

    @Override
    public ModelPart root() {{
        return this.root;
    }}

    @Override
    public void setupAnim(T entity, float limbSwing, float limbSwingAmount, float ageInTicks, float netHeadYaw, float headPitch) {{
        this.root().getAllParts().forEach(ModelPart::resetPose);

        float phase = limbSwing * 0.6662F;
        float amount = Math.min(limbSwingAmount, 1.0F);

        // legs: opposite phase
        this.rightLeg.xRot = Mth.cos(phase) * STRIDE * amount;
        this.leftLeg.xRot = Mth.cos(phase + Mth.PI) * STRIDE * amount;

        // arms swing opposite to the leg on the same side; the sword arm swings less
        this.rightArm.xRot = Mth.cos(phase + Mth.PI) * ARM_SWING * amount * SWORD_ARM_FACTOR;
        this.leftArm.xRot = Mth.cos(phase) * ARM_SWING * amount * FREE_ARM_FACTOR;
        float idle = Mth.cos(ageInTicks * 0.06F) * 0.03F + 0.03F;
        this.rightArm.zRot += idle;
        this.leftArm.zRot -= idle;

        // heavy gait: the upper body sinks on each footfall (+y is down) and sways over the planted leg
        float bob = Mth.abs(Mth.cos(phase)) * BOB * amount + Mth.sin(ageInTicks * 0.06F) * 0.25F;
        this.body.y += bob;
        this.head.y += bob;
        this.rightArm.y += bob;
        this.leftArm.y += bob;
        this.body.zRot = Mth.cos(phase) * 0.04F * amount;

        // head follows look direction
        this.head.yRot = netHeadYaw * Mth.DEG_TO_RAD;
        this.head.xRot = headPitch * Mth.DEG_TO_RAD;
    }}
}}
'''
open(os.path.join(OUT, 'ColossusModel.java'), 'w').write(java)

eyes_java = '''package net.colossus.client.model;

import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.world.entity.Entity;

/** Full-bright glowing eye slits: renders colossus_eyes.png (only the two eye texels are opaque) with RenderType.eyes. */
public class ColossusEyesLayer<T extends Entity> extends EyesLayer<T, ColossusModel<T>> {
    private static final RenderType EYES = RenderType.eyes(ColossusModel.EYES_TEXTURE);

    public ColossusEyesLayer(RenderLayerParent<T, ColossusModel<T>> parent) {
        super(parent);
    }

    @Override
    public RenderType renderType() {
        return EYES;
    }
}
'''
open(os.path.join(OUT, 'ColossusEyesLayer.java'), 'w').write(eyes_java)

# ---------------------------------------------------------------- bbmodel
def uid():
    return str(uuid.uuid4())

def bb_origin(bone):
    x, H, z = B.BONES[bone]['pivot']
    return [-x, H, z]

elements = []
def bb_group(bone):
    b = B.BONES[bone]
    rx, ry, rz = b['rot']
    kids = []
    for p in B.PARTS:
        if p['bone'] != bone: continue
        _, _, w, h, d = B.footprint(p)
        u, v = p['u'], p['v']
        e = {
            'name': p['name'], 'box_uv': True, 'rescale': False, 'locked': False, 'light_emission': 0,
            'render_order': 'default', 'allow_mirror_modeling': True,
            'from': [-p['x1'], p['H0'], p['z0']], 'to': [-p['x0'], p['H1'], p['z1']],
            'autouv': 0, 'color': 0, 'origin': bb_origin(bone), 'uv_offset': [u, v],
            'faces': {
                'north': {'uv': [u + d, v + d, u + d + w, v + d + h], 'texture': 0},
                'east': {'uv': [u, v + d, u + d, v + d + h], 'texture': 0},
                'south': {'uv': [u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h], 'texture': 0},
                'west': {'uv': [u + d + w, v + d, u + 2 * d + w, v + d + h], 'texture': 0},
                'up': {'uv': [u + d + w, v + d, u + d, v], 'texture': 0},
                'down': {'uv': [u + d + 2 * w, v, u + d + w, v + d], 'texture': 0},
            },
            'type': 'cube', 'uuid': uid(),
        }
        elements.append(e)
        kids.append(e['uuid'])
    for c in children(bone):
        kids.append(bb_group(c))
    return {'name': bone, 'origin': bb_origin(bone),
            'rotation': [-math.degrees(rx), -math.degrees(ry), math.degrees(rz)],
            'color': 0, 'uuid': uid(), 'export': True, 'mirror_uv': False, 'isOpen': True, 'locked': False,
            'visibility': True, 'autouv': 0, 'children': kids}

outliner = [bb_group('root')]

def tex_entry(path, name, idx):
    data = base64.b64encode(open(path, 'rb').read()).decode()
    return {'path': '', 'name': name, 'folder': '', 'namespace': '', 'id': str(idx), 'group': '',
            'width': B.TW, 'height': B.TH, 'uv_width': B.TW, 'uv_height': B.TH, 'particle': idx == 0,
            'use_as_default': idx == 0, 'layers_enabled': False, 'sync_to_project': '', 'render_mode': 'default',
            'render_sides': 'auto', 'pbr_channel': 'color', 'frame_time': 1, 'frame_order_type': 'loop',
            'frame_order': '', 'frame_interpolate': False, 'visible': True, 'internal': True, 'saved': True,
            'uuid': uid(), 'relative_path': '', 'source': 'data:image/png;base64,' + data}

bb = {
    'meta': {'format_version': '4.10', 'model_format': 'modded_entity', 'box_uv': True},
    'name': 'colossus', 'model_identifier': '', 'modded_entity_entity_class': 'T',
    'modded_entity_version': '1.17', 'modded_entity_flip_y': True,
    'visible_box': [1.5, 3.3, 0], 'variable_placeholders': '', 'variable_placeholder_buttons': [],
    'timeline_setups': [], 'unhandled_root_fields': {},
    'resolution': {'width': B.TW, 'height': B.TH},
    'elements': elements, 'outliner': outliner,
    'textures': [tex_entry(os.path.join(OUT, 'colossus.png'), 'colossus.png', 0)],
}
json.dump(bb, open(os.path.join(OUT, 'colossus.bbmodel'), 'w'), indent=1)
print('java + bbmodel written;', len(B.PARTS), 'cubes')
