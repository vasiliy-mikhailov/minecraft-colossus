package com.colossus.client;

import com.colossus.Colossus;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Client-only wiring: renderer + model layer. Never loaded on a dedicated server. */
@EventBusSubscriber(modid = Colossus.MODID, value = Dist.CLIENT)
public final class ColossusClient {
    private ColossusClient() {}

    @SubscribeEvent
    static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(ColossusModel.LAYER, ColossusModel::createBodyLayer);
    }

    @SubscribeEvent
    static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(Colossus.COLOSSUS.get(), ColossusRenderer::new);
        Colossus.LOGGER.info("[colossus] renderer registered");
    }
}
