package com.colossus;

import com.mojang.logging.LogUtils;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.DeferredSpawnEggItem;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import org.slf4j.Logger;

/** Common (both sides) registration: entity type, attributes, spawn egg. */
@Mod(Colossus.MODID)
public class Colossus {
    public static final String MODID = "colossus";
    public static final Logger LOGGER = LogUtils.getLogger();

    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(Registries.ENTITY_TYPE, MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(MODID);

    public static final DeferredHolder<EntityType<?>, EntityType<ColossusEntity>> COLOSSUS =
            ENTITY_TYPES.register("colossus", () -> EntityType.Builder
                    .of(ColossusEntity::new, MobCategory.CREATURE)
                    .sized(1.5F, 3.3F)          // hitbox: model is 52 px (3.25 blocks) tall incl. crest, 29 px wide
                    .eyeHeight(2.75F)          // eye slits at 43 px
                    .clientTrackingRange(10)
                    .build("colossus"));

    public static final DeferredItem<DeferredSpawnEggItem> COLOSSUS_SPAWN_EGG =
            ITEMS.register("colossus_spawn_egg",
                    () -> new DeferredSpawnEggItem(COLOSSUS, 0x6E6E6E, 0xD4A017, new Item.Properties()));

    public Colossus(IEventBus modEventBus, ModContainer modContainer) {
        ENTITY_TYPES.register(modEventBus);
        ITEMS.register(modEventBus);
        modEventBus.addListener(this::registerAttributes);
        modEventBus.addListener(this::addCreative);
        LOGGER.info("[colossus] mod constructed");
    }

    private void registerAttributes(EntityAttributeCreationEvent event) {
        event.put(COLOSSUS.get(), ColossusEntity.createAttributes().build());
        LOGGER.info("[colossus] attributes registered");
    }

    private void addCreative(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) {
            event.accept(COLOSSUS_SPAWN_EGG);
        }
    }
}
