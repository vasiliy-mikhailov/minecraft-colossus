package com.colossus.client;

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
import com.colossus.ColossusEntity;

/**
 * Colossus - blocky armoured knight, ~1.6x player height (52 px tall, 128x128 texture).
 * NeoForge / Minecraft 1.21.1, Mojang mappings. Ground is at model y = 24 (standard living-entity origin),
 * so the renderer needs no extra scale/translate. Bones: root -> body, head, right_arm (-> sword), left_arm,
 * right_leg, left_leg. Generated from colossus.bbmodel geometry (Blockbench "Modded Entity", flip-Y).
 */
public class ColossusModel extends HierarchicalModel<ColossusEntity> {
    public static final ModelLayerLocation LAYER_LOCATION =
            new ModelLayerLocation(ResourceLocation.fromNamespaceAndPath("colossus", "colossus"), "main");
    public static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath("colossus", "textures/entity/colossus.png");
    public static final ResourceLocation EYES_TEXTURE =
            ResourceLocation.fromNamespaceAndPath("colossus", "textures/entity/colossus_eyes.png");
    /** Layer id used by ColossusClient (alias of LAYER_LOCATION). */
    public static final ModelLayerLocation LAYER = LAYER_LOCATION;

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

    public ColossusModel(ModelPart root) {
        this.root = root;
        ModelPart colossus = root.getChild("root");
        this.body = colossus.getChild("body");
        this.head = colossus.getChild("head");
        this.rightArm = colossus.getChild("right_arm");
        this.leftArm = colossus.getChild("left_arm");
        this.sword = this.rightArm.getChild("sword");
        this.rightLeg = colossus.getChild("right_leg");
        this.leftLeg = colossus.getChild("left_leg");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition meshdefinition = new MeshDefinition();
        PartDefinition partdefinition = meshdefinition.getRoot();

        PartDefinition p_root = partdefinition.addOrReplaceChild("root", CubeListBuilder.create()
                , PartPose.offset(0.0F, 24.0F, 0.0F));
        PartDefinition p_body = p_root.addOrReplaceChild("body", CubeListBuilder.create()
                .texOffs(0, 0).addBox(-8.0F, -18.0F, -5.5F, 16.0F, 8.0F, 10.0F) // chest
                .texOffs(72, 64).addBox(-7.0F, -10.0F, -5.0F, 14.0F, 3.0F, 9.0F) // ribs
                .texOffs(14, 77).addBox(-6.0F, -7.0F, -4.5F, 12.0F, 3.0F, 8.0F) // waist
                .texOffs(0, 50).addBox(-7.0F, -4.0F, -5.0F, 14.0F, 4.0F, 10.0F) // belt
                .texOffs(20, 98).addBox(-3.0F, -3.5F, -6.0F, 6.0F, 3.0F, 1.0F) // buckle
                .texOffs(0, 77).addBox(-3.0F, 0.0F, -5.0F, 6.0F, 11.0F, 1.0F) // tabard
                .texOffs(20, 89).addBox(-7.0F, -15.0F, 4.5F, 14.0F, 7.0F, 1.0F) // back_plate
                .texOffs(78, 18).addBox(-4.0F, -4.0F, 5.0F, 8.0F, 14.0F, 1.0F) // back_tabard
                , PartPose.offset(0.0F, -21.0F, 0.0F));
        PartDefinition p_head = p_root.addOrReplaceChild("head", CubeListBuilder.create()
                .texOffs(52, 0).addBox(-4.0F, -9.0F, -5.5F, 8.0F, 9.0F, 8.0F) // helm
                .texOffs(50, 89).addBox(-1.5F, -14.0F, -3.5F, 3.0F, 5.0F, 2.0F) // crest1
                .texOffs(60, 89).addBox(-1.5F, -13.5F, -1.5F, 3.0F, 5.0F, 1.0F) // crest2
                .texOffs(68, 89).addBox(-1.5F, -13.0F, -0.5F, 3.0F, 5.0F, 1.0F) // crest3
                .texOffs(76, 89).addBox(-1.5F, -12.5F, 0.5F, 3.0F, 5.0F, 1.0F) // crest4
                .texOffs(84, 89).addBox(-1.5F, -12.0F, 1.5F, 3.0F, 5.0F, 1.0F) // crest5
                .texOffs(92, 89).addBox(-1.5F, -11.0F, 2.5F, 3.0F, 5.0F, 1.0F) // crest6
                .texOffs(100, 89).addBox(-1.5F, -10.0F, 3.5F, 3.0F, 5.0F, 1.0F) // crest7
                .texOffs(108, 89).addBox(-1.5F, -9.0F, 4.5F, 3.0F, 5.0F, 1.0F) // crest8
                .texOffs(116, 89).addBox(-1.5F, -8.0F, 5.5F, 3.0F, 5.0F, 1.0F) // crest9
                , PartPose.offset(0.0F, -38.0F, -1.0F));
        PartDefinition p_right_arm = p_root.addOrReplaceChild("right_arm", CubeListBuilder.create()
                .texOffs(84, 0).addBox(-3.0F, -3.0F, -4.5F, 6.0F, 8.0F, 9.0F) // right_pauldron
                .texOffs(102, 77).addBox(-2.5F, 5.0F, -2.5F, 5.0F, 4.0F, 5.0F) // right_mail
                .texOffs(48, 50).addBox(-4.0F, 9.0F, -3.5F, 7.0F, 6.0F, 7.0F) // right_bracer
                .texOffs(54, 77).addBox(-3.5F, 15.0F, -2.5F, 5.0F, 5.0F, 5.0F) // right_hand
                , PartPose.offset(-11.0F, -36.0F, -0.5F));
        PartDefinition p_sword = p_right_arm.addOrReplaceChild("sword", CubeListBuilder.create()
                .texOffs(94, 77).addBox(-1.0F, -3.5F, -1.0F, 2.0F, 8.0F, 2.0F) // grip
                .texOffs(0, 98).addBox(-3.5F, 4.5F, -1.5F, 7.0F, 2.0F, 3.0F) // guard
                .texOffs(90, 35).addBox(-2.0F, 6.5F, -1.0F, 4.0F, 13.0F, 2.0F) // blade
                , PartPose.offsetAndRotation(-1.0F, 17.5F, 0.0F, -0.7F, 0.0F, 0.18F));
        PartDefinition p_left_arm = p_root.addOrReplaceChild("left_arm", CubeListBuilder.create()
                .texOffs(0, 18).addBox(-3.0F, -3.0F, -4.5F, 6.0F, 8.0F, 9.0F) // left_pauldron
                .texOffs(0, 89).addBox(-2.5F, 5.0F, -2.5F, 5.0F, 4.0F, 5.0F) // left_mail
                .texOffs(76, 50).addBox(-3.0F, 9.0F, -3.5F, 7.0F, 6.0F, 7.0F) // left_bracer
                .texOffs(74, 77).addBox(-1.5F, 15.0F, -2.5F, 5.0F, 5.0F, 5.0F) // left_hand
                , PartPose.offset(11.0F, -36.0F, -0.5F));
        PartDefinition p_right_leg = p_root.addOrReplaceChild("right_leg", CubeListBuilder.create()
                .texOffs(30, 18).addBox(-3.0F, 0.0F, -3.0F, 6.0F, 11.0F, 6.0F) // right_thigh
                .texOffs(96, 18).addBox(-3.5F, 0.0F, -4.0F, 7.0F, 7.0F, 8.0F) // right_tasset
                .texOffs(0, 35).addBox(-3.5F, 11.0F, -4.0F, 7.0F, 7.0F, 8.0F) // right_shin
                .texOffs(0, 64).addBox(-4.5F, 18.0F, -5.5F, 8.0F, 3.0F, 10.0F) // right_boot
                , PartPose.offset(-4.5F, -21.0F, 0.0F));
        PartDefinition p_left_leg = p_root.addOrReplaceChild("left_leg", CubeListBuilder.create()
                .texOffs(54, 18).addBox(-3.0F, 0.0F, -3.0F, 6.0F, 11.0F, 6.0F) // left_thigh
                .texOffs(30, 35).addBox(-3.5F, 0.0F, -4.0F, 7.0F, 7.0F, 8.0F) // left_tasset
                .texOffs(60, 35).addBox(-3.5F, 11.0F, -4.0F, 7.0F, 7.0F, 8.0F) // left_shin
                .texOffs(36, 64).addBox(-3.5F, 18.0F, -5.5F, 8.0F, 3.0F, 10.0F) // left_boot
                , PartPose.offset(4.5F, -21.0F, 0.0F));

        return LayerDefinition.create(meshdefinition, 128, 128);
    }

    @Override
    public ModelPart root() {
        return this.root;
    }

    @Override
    public void setupAnim(ColossusEntity entity, float limbSwing, float limbSwingAmount, float ageInTicks, float netHeadYaw, float headPitch) {
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
    }
}
