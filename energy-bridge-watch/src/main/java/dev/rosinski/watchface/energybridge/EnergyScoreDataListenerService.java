package dev.rosinski.watchface.energybridge;

import android.content.ComponentName;

import androidx.wear.watchface.complications.datasource.ComplicationDataSourceUpdateRequester;

import com.google.android.gms.wearable.DataEvent;
import com.google.android.gms.wearable.DataEventBuffer;
import com.google.android.gms.wearable.DataMapItem;
import com.google.android.gms.wearable.WearableListenerService;

/** Receives a score from the paired phone and asks Wear OS to redraw it. */
public final class EnergyScoreDataListenerService extends WearableListenerService {
    static final String PATH = "/nine-eleven/energy-score";

    @Override
    public void onDataChanged(DataEventBuffer events) {
        for (DataEvent event : events) {
            if (event.getType() != DataEvent.TYPE_CHANGED || !PATH.equals(event.getDataItem().getUri().getPath())) {
                continue;
            }
            int score = DataMapItem.fromDataItem(event.getDataItem()).getDataMap().getInt("score", -1);
            EnergyScoreStore.save(this, score);
            ComplicationDataSourceUpdateRequester
                    .create(this, new ComponentName(this, EnergyScoreComplicationService.class))
                    .requestUpdateAll();
        }
    }
}
