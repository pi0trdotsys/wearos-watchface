package dev.rosinski.watchface.energybridge;

import android.os.RemoteException;
import androidx.wear.watchface.complications.data.ComplicationData;
import androidx.wear.watchface.complications.data.ComplicationType;
import androidx.wear.watchface.complications.data.PlainComplicationText;
import androidx.wear.watchface.complications.data.ShortTextComplicationData;
import androidx.wear.watchface.complications.datasource.ComplicationDataSourceService;
import androidx.wear.watchface.complications.datasource.ComplicationRequest;

/** Selectable watch-side provider. The phone bridge pushes score updates. */
public final class EnergyScoreComplicationService extends ComplicationDataSourceService {
    @Override
    public void onComplicationRequest(
            ComplicationRequest request,
            ComplicationRequestListener listener) {
        try {
            listener.onComplicationData(dataFor(EnergyScoreStore.read(this)));
        } catch (RemoteException ignored) {
            // The system cancelled the request before it could be delivered.
        }
    }

    @Override
    public ComplicationData getPreviewData(ComplicationType type) {
        return dataFor(84);
    }

    private ComplicationData dataFor(int score) {
        String text = score >= 0 && score <= 100 ? Integer.toString(score) : "--";
        PlainComplicationText complicationText =
                new PlainComplicationText.Builder(text).build();
        return new ShortTextComplicationData.Builder(complicationText, complicationText).build();
    }
}
