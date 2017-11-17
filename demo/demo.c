#include <gst/gst.h>
#include <stdio.h>

static void on_full_final_result(GstBus *bus, gchar *msg, GstMessage *mes) {
    g_print("%s", msg);
}

static void on_final_result(GstBus *bus, gchar *msg, ...) {
    g_print("%s\n", msg);
}

int main(int argc, char* argv[]) {
    GMainLoop *loop;

    GstElement *filesrc,
               *decodebin,
               *audioconvert,
               *audioresample,
               *asr,
               *filesink,
               *pipeline;

    gst_init(&argc, &argv);

    loop = g_main_loop_new (NULL, FALSE);

    pipeline = gst_pipeline_new(NULL); g_assert(pipeline);
    filesrc = gst_element_factory_make("filesrc", NULL); g_assert(filesrc);
    decodebin = gst_element_factory_make("mad", NULL); g_assert(decodebin);
    audioconvert = gst_element_factory_make("audioconvert", NULL); g_assert(audioconvert);
    audioresample = gst_element_factory_make("audioresample", NULL); g_assert(audioresample);
    filesink = gst_element_factory_make("fakesink", NULL); g_assert(filesink);
    asr = gst_element_factory_make("kaldinnet2onlinedecoder", NULL); g_assert(asr);

    // setup filesrc
    g_object_set(G_OBJECT(filesrc), "location", "dr_strangelove.mp3", NULL);

    // setup asr
    g_object_set(G_OBJECT(asr), "use-threaded-decoder", TRUE, NULL);
    g_object_set(G_OBJECT(asr), "model", "final.mdl", NULL);
    g_object_set(G_OBJECT(asr), "fst", "HCLG.fst", NULL);
    g_object_set(G_OBJECT(asr), "word-syms", "words.txt", NULL);
    g_object_set(G_OBJECT(asr), "phone-syms", "phones.txt", NULL);
    g_object_set(G_OBJECT(asr), "word-boundary-file", "word_boundary.int", NULL);
    g_object_set(G_OBJECT(asr), "num-nbest", 3, NULL);
    g_object_set(G_OBJECT(asr), "num-phone-alignment", 3, NULL);
    g_object_set(G_OBJECT(asr), "do-phone-alignment", TRUE, NULL);
    g_object_set(G_OBJECT(asr), "feature-type", "mfcc", NULL);
    g_object_set(G_OBJECT(asr), "mfcc-config", "conf/mfcc.conf", NULL);
    g_object_set(G_OBJECT(asr), "ivector-extraction-config", "conf/ivector_extractor.fixed.conf", NULL);
    g_object_set(G_OBJECT(asr), "max-active", 7000, NULL);
    g_object_set(G_OBJECT(asr), "beam", 11.0, NULL);
    g_object_set(G_OBJECT(asr), "lattice-beam", 5.0, NULL);
    g_object_set(G_OBJECT(asr), "do-endpointing", TRUE, NULL);
    g_object_set(G_OBJECT(asr), "endpoint-silence-phones", "1:2:3:4:5:6:7:8:9:10", NULL);
    g_object_set(G_OBJECT(asr), "chunk-length-in-secs", 0.2, NULL);

    gst_bin_add_many(GST_BIN(pipeline), filesrc, decodebin, audioconvert, audioresample, asr, filesink, NULL);

    if (!gst_element_link(filesrc, decodebin))
        g_error("Failed to link filesrc to decodebin");

    if (!gst_element_link(decodebin, audioconvert))
        g_error("Failed to link decodebin to audioconvert");

    if (!gst_element_link(audioconvert, audioresample))
        g_error("Failed to link audioconvert to audioresample");

    if (!gst_element_link(audioresample, asr))
        g_error("Failed to link audioresample to asr!");

    if (!gst_element_link(asr, filesink))
        g_error("Failed to link asr to filesink");

    // g_signal_connect(asr, "full-final-result", G_CALLBACK(on_full_final_result), NULL);
    g_signal_connect(asr, "final-result", G_CALLBACK(on_final_result), NULL);
    gst_element_set_state (pipeline, GST_STATE_PLAYING);
    gst_element_set_state (filesrc, GST_STATE_PLAYING);


    g_print("Running...\n");
    g_main_loop_run(loop);

    g_print("Finished, cleaning up...");
    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(pipeline);
    g_main_loop_unref(loop);
    return 0;
}
