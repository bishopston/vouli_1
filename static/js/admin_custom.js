(function($){
    $(document).ready(function(){
        // Apply datepicker to all date fields
        $('.vDateField').datepicker();

        // Function to update the timeslot options based on the selected date
        function updateTimeslots() {
            // Get the selected date value
            var selectedDate = $('#id_date').val();

            // Make an AJAX request to get the filtered timeslots
            $.ajax({
                type: 'GET',
                url: "{% url 'reservations:get_timeslots' %}",
                
                data: {
                    'date': selectedDate,
                },
                success: function (data) {
                    // Log the received data to the console
                    console.log('Received data:', data);
                
                    // Update the timeslot options
                    $('#id_timeslot').html(data);
                },
                error: function (xhr, status, error) {
                    console.error('Error fetching timeslots:', status, error);
                
                    // Optionally, you can log the response text for more details
                    console.log('Response text:', xhr.responseText);
                }
            });
        }

        // Bind the updateTimeslots function to the date field change event
        $('#id_date').change(updateTimeslots);

        // Call updateTimeslots on page load
        updateTimeslots();
    });
})(django.jQuery);